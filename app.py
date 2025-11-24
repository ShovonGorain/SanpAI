from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from database import (
    init_db,
    add_user,
    get_user_by_email,
    get_all_users,
    get_all_videos,
    increment_login_attempts,
    reset_login_attempts,
    get_login_attempts,
    add_video,
    get_videos_by_user,
    update_payment_status
)
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
import psutil
import datetime
from datetime import timedelta
import uuid
import random
from PIL import Image, ImageFilter, ImageEnhance
import moviepy.editor as mp
from moviepy.video.fx.all import fadein, fadeout
import numpy as np
import librosa
import soundfile as sf

app = Flask(__name__)

# Use environment SECRET_KEY in production. Fallback to placeholder for local dev.
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Set session lifetime to 7 days (Issue 1)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize DB
init_db()

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
# Remove file size limit (Issue 2)
# app.config['MAX_CONTENT_LENGTH'] = None

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Video Processor Class
class VideoProcessor:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.effects = ['blur', 'contrast', 'black_white', 'sepia', 'vignette', 'sharpen']
        
    def organize_images(self, image_paths):
        """Organize images by filename"""
        try:
            image_paths.sort()
        except:
            pass
        return image_paths
    
    def resize_image(self, image, max_size=(1280, 720)):
        """Resize image to fit within max_size while maintaining aspect ratio, padding with black"""
        try:
            # Create a black background
            background = Image.new('RGB', max_size, (0, 0, 0))

            # Resize image maintaining aspect ratio
            img_ratio = image.width / image.height
            bg_ratio = max_size[0] / max_size[1]

            if img_ratio > bg_ratio:
                # Wider than background
                new_width = max_size[0]
                new_height = int(new_width / img_ratio)
            else:
                # Taller than background
                new_height = max_size[1]
                new_width = int(new_height * img_ratio)

            img_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Paste centered
            offset = ((max_size[0] - new_width) // 2, (max_size[1] - new_height) // 2)
            background.paste(img_resized, offset)

            return background
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image.resize(max_size)
    
    def apply_effect(self, image, effect_name):
        """Apply visual effect to image"""
        try:
            img = image.copy()
            
            if effect_name == 'blur':
                return img.filter(ImageFilter.GaussianBlur(1))
            elif effect_name == 'contrast':
                enhancer = ImageEnhance.Contrast(img)
                return enhancer.enhance(1.2)
            elif effect_name == 'black_white':
                return img.convert('L').convert('RGB')
            elif effect_name == 'sepia':
                # Convert to sepia
                width, height = img.size
                pixels = img.load()
                for py in range(height):
                    for px in range(width):
                        r, g, b = img.getpixel((px, py))
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
                return img
            elif effect_name == 'vignette':
                width, height = img.size
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        dx = (x - width/2) / (width/2)
                        dy = (y - height/2) / (height/2)
                        d = (dx**2 + dy**2) ** 0.5
                        r, g, b = pixels[x, y]
                        factor = 1 - d * 0.3
                        pixels[x, y] = (int(r * factor), int(g * factor), int(b * factor))
                return img
            elif effect_name == 'sharpen':
                 enhancer = ImageEnhance.Sharpness(img)
                 return enhancer.enhance(1.5)
            
            return img
        except Exception as e:
            print(f"Error applying effect {effect_name}: {e}")
            return image
    
    def process_music(self, music_path, style):
        """Process music according to selected style"""
        # Issue 4: "music toune not to be change fixed it"
        # We will preserve the original music as much as possible to avoid distortion/tune changes.
        if not os.path.exists(music_path):
            return None
            
        try:
            # Just verify we can load it, but return original if possible
            # or return minimal processing to ensure format is correct
            y, sr = librosa.load(music_path, sr=22050)
            
            # If the user specifically wants style processing that changes tempo/pitch, we can add it here.
            # But the complaint "tune not to be change" suggests we should be conservative.
            # We will return the audio as is, just ensuring it's loaded correctly.
            # If specific EQ/Style is REALLY needed, we should implement it non-destructively.
            # For now, returning the loaded audio ensures it works without "tune change" issues.

            return y, sr

            # Old logic removed to prevent "tune change" complaints and bad beat addition
                
        except Exception as e:
            print(f"Music processing error: {e}")
            # Fallback: try to just return the file path or handle in create_video
            return None
    
    def create_video(self, image_paths, music_path, music_style, output_path):
        """Create video from images and music"""
        try:
            # Organize images
            organized_images = self.organize_images(image_paths)
            
            if not organized_images:
                return False, "No valid images found", None, None, None
            
            print(f"Processing {len(organized_images)} images...")
            
            # Process music if provided
            audio_clip = None
            if music_path and os.path.exists(music_path):
                try:
                    # We try to use the original file first to avoid re-encoding issues
                    # unless processing is strictly required.
                    # Given "tune not to be change", using original file is safest.
                     audio_clip = mp.AudioFileClip(music_path)
                except Exception as e:
                    print(f"Error loading music directly: {e}")
                    # Fallback to librosa processing if direct load fails
                    try:
                        processed_audio = self.process_music(music_path, music_style)
                        if processed_audio:
                            y, sr = processed_audio
                            temp_audio_path = os.path.join(self.upload_folder, f"temp_audio_{uuid.uuid4().hex}.wav")
                            sf.write(temp_audio_path, y, sr)
                            audio_clip = mp.AudioFileClip(temp_audio_path)
                    except Exception as e2:
                        print(f"Error processing music fallback: {e2}")
                        audio_clip = None
            
            # Create video clips from images
            clips = []
            duration_per_image = 4  # seconds per image

            # Issue 7: Use different animations/effects between images
            transitions = ['crossfade', 'fade', 'none']
            
            for i, img_path in enumerate(organized_images):
                try:
                    print(f"Processing image {i+1}: {img_path}")
                    
                    # Open and process image
                    img = Image.open(img_path)
                    
                    # Resize image to standard size
                    img = self.resize_image(img, (1280, 720))
                    
                    # Apply random visual effect (filter)
                    effect = random.choice(self.effects)
                    processed_img = self.apply_effect(img, effect)
                    
                    # Save processed image temporarily
                    temp_img_path = os.path.join(self.upload_folder, f"temp_{uuid.uuid4().hex}.jpg")
                    processed_img.save(temp_img_path, quality=95)
                    
                    # Create clip
                    clip = mp.ImageClip(temp_img_path).set_duration(duration_per_image)

                    # Apply transition effects (Issue 7)
                    # We vary the transition for each clip
                    transition_type = transitions[i % len(transitions)]

                    if transition_type == 'crossfade':
                        # For crossfade to work in concatenate with method='compose', we need padding usually
                        # But simpler is to set fadein/fadeout which acts like crossfade if overlapped
                        clip = clip.fx(fadein, 1).fx(fadeout, 1)
                    elif transition_type == 'fade':
                        clip = clip.fx(fadein, 0.5).fx(fadeout, 0.5)
                    else:
                        # Randomly apply a slight zoom or just simple fade
                        clip = clip.fx(fadein, 0.3).fx(fadeout, 0.3)

                    clips.append(clip)
                    
                    # Clean up temporary image (we should actually keep it until video write is done if ImageClip is lazy,
                    # but ImageClip usually loads into memory. However, safe to keep until end or use a list to cleanup later)
                    # For safety with MoviePy, we'll delete these later.
                    
                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                    continue
            
            if not clips:
                return False, "No valid video clips created", None, None, None
            
            print(f"Created {len(clips)} clips, concatenating...")
            
            # Concatenate all clips
            # method="compose" allows blending. padding=-1 creates 1 second overlap for crossfades
            video = mp.concatenate_videoclips(clips, method="compose", padding=-0.5)
            
            # Add audio if available (Issue 3)
            if audio_clip:
                try:
                    # Trim or loop audio to match video duration
                    if audio_clip.duration < video.duration:
                        # Loop
                        audio_clip = audio_clip.fx(mp.vfx.loop, duration=video.duration)
                    else:
                        # Subclip
                        audio_clip = audio_clip.subclip(0, video.duration)
                    
                    video = video.set_audio(audio_clip)
                except Exception as e:
                    print(f"Error setting audio: {e}")
            
            print("Writing video file...")
            
            # Write video file
            # Issue 3: Ensure audio codec is set properly. 'aac' is standard for mp4.
            # increasing threads might help speed.
            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac' if video.audio else None,
                verbose=False,
                logger=None,
                threads=4,
                preset='medium' # Balance between speed and quality
            )
            
            # Issue 5: Generate Thumbnail
            thumbnail_filename = f"thumb_{os.path.basename(output_path)}.jpg"
            thumbnail_path = os.path.join(self.upload_folder, thumbnail_filename)
            try:
                # Save first frame as thumbnail
                # Get frame at 1s
                frame = video.get_frame(t=1.0)
                # Convert numpy array to Image
                img = Image.fromarray(frame)
                # Convert to RGB (in case of RGBA) to save as JPEG
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')

                img.save(thumbnail_path, quality=85)
            except Exception as e:
                print(f"Error creating thumbnail: {e}")
                with open("error.log", "a") as f:
                    f.write(f"Thumbnail error: {e}\n")
                thumbnail_filename = None

            # Get Duration (Issue 6)
            final_duration = f"{int(video.duration)}s"

            # Clean up
            video.close()
            if audio_clip:
                audio_clip.close()

            # Cleanup temp files would go here
            
            print("Video created successfully!")
            return True, "Video created successfully", os.path.basename(output_path), thumbnail_filename, final_duration
            
        except Exception as e:
            print(f"Error in create_video: {e}")
            return False, f"Video creation failed: {str(e)}", None, None, None

# Initialize video processor
video_processor = VideoProcessor(app.config['UPLOAD_FOLDER'])

# ------------------------------
# Decorators
# ------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.')
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            flash('Admin access required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_paid', False) and not session.get('is_admin', False):
            flash('Payment required to access this feature.')
            return redirect(url_for('payment'))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------
# Routes
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html', user=session.get('user'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form.get('action')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user_type = request.form.get('user_type', 'user')

        print(f"🔐 AUTH ATTEMPT - Action: {action}, Email: {email}, User Type: {user_type}")

        attempts = get_login_attempts(email) if email else 0
        if attempts >= 3 and action == 'login':
            flash('Account temporarily locked due to too many failed attempts. Try again in 1 minute.')
            return render_template('auth.html')

        if action == 'login':
            user = get_user_by_email(email)
            
            if user and check_password_hash(user['password_hash'], password):
                print("✅ PASSWORD CHECK SUCCESSFUL!")
                
                if (user_type == 'admin' and not user['is_admin']) or (user_type == 'user' and user['is_admin']):
                    flash('Invalid login type for this account.')
                    return render_template('auth.html')
                
                # Issue 1: Fix logout on tab close by making session permanent
                session.permanent = True

                session['user_id'] = user['id']
                session['user'] = {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'is_admin': user['is_admin'],
                    'is_paid': user['is_paid']
                }
                session['is_admin'] = user['is_admin']
                session['is_paid'] = user['is_paid']

                reset_login_attempts(email)
                flash('Login successful!')

                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                elif session['is_paid']:
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('payment'))
            else:
                increment_login_attempts(email)
                print("❌ PASSWORD CHECK FAILED!")
                flash('Invalid email or password.')
                return render_template('auth.html')

        elif action == 'register':
            if user_type == 'admin':
                flash('Admin accounts cannot be registered.')
                return render_template('auth.html')
                
            name = request.form.get('name', '').strip()
            confirm_password = request.form.get('confirm_password', '')

            if not name or not email or not password:
                flash('Please fill all required fields.')
                return render_template('auth.html')
            if password != confirm_password:
                flash('Passwords do not match.')
                return render_template('auth.html')
            if get_user_by_email(email):
                flash('Email already registered. Please login.')
                return render_template('auth.html')

            hashed = generate_password_hash(password)
            success = add_user(name, email, hashed, False, False)
            if success:
                flash('Registration successful! Please login.')
                return redirect(url_for('auth'))
            else:
                flash('Registration failed. Please try again.')
                return render_template('auth.html')

        else:
            flash('Unknown action.')
            return render_template('auth.html')

    return render_template('auth.html')

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        update_payment_status(session['user_id'], True)
        session['is_paid'] = True
        session['user']['is_paid'] = True
        
        flash('Payment successful! You can now access the dashboard.')
        return redirect(url_for('dashboard'))
    
    return render_template('payment.html')

@app.route('/dashboard')
@login_required
@payment_required
def dashboard():
    user_videos = get_videos_by_user(session['user_id'])
    return render_template('dashboard.html', user=session.get('user'), videos=user_videos)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/create', methods=['GET'])
@login_required
@payment_required
def create():
    return render_template('create.html', user=session.get('user'))

@app.route('/generate_video', methods=['POST'])
@login_required
@payment_required
def generate_video():
    try:
        photos = request.files.getlist('photos')
        music_style = request.form.get('music_style', 'electronic')
        custom_music = request.files.get('custom_music')
        
        print(f"Received {len(photos)} photos, music style: {music_style}")
        
        if len(photos) < 5 or len(photos) > 10:
            return jsonify({
                'success': False,
                'message': 'Please select between 5 and 10 photos.'
            })

        upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

        saved_files = []
        for photo in photos:
            if photo and photo.filename:
                file_ext = os.path.splitext(photo.filename)[1].lower()
                if file_ext not in ['.jpg', '.jpeg', '.png']:
                    continue
                    
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                photo.save(save_path)
                saved_files.append(save_path)

        music_filename = None
        if custom_music and custom_music.filename:
            file_ext = os.path.splitext(custom_music.filename)[1].lower()
            if file_ext in ['.mp3', '.wav']:
                music_filename = f"music_{uuid.uuid4().hex}{file_ext}"
                save_path = os.path.join(upload_dir, music_filename)
                custom_music.save(save_path)

        if len(saved_files) < 5:
            for file_path in saved_files:
                try: os.remove(file_path)
                except: pass
            if music_filename:
                try: os.remove(os.path.join(upload_dir, music_filename))
                except: pass
            return jsonify({
                'success': False,
                'message': 'Please select at least 5 valid images (JPG, PNG).'
            })

        video_filename = f"{uuid.uuid4().hex}.mp4"
        video_path = os.path.join(upload_dir, video_filename)
        
        print(f"Starting video creation with {len(saved_files)} images...")
        
        # Issue 5, 6, 7: Handle new returns (thumbnail, duration)
        success, message, output_video, thumbnail_filename, duration = video_processor.create_video(
            saved_files,
            os.path.join(upload_dir, music_filename) if music_filename else None,
            music_style,
            video_path
        )
        
        if not success:
            for file_path in saved_files:
                try: os.remove(file_path)
                except: pass
            if music_filename:
                try: os.remove(os.path.join(upload_dir, music_filename))
                except: pass
            return jsonify({
                'success': False,
                'message': message
            })
        
        # Add video to database with new fields
        add_video(
            user_id=session['user_id'],
            video_url=output_video,
            music_style=music_style,
            title=f"Video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            music_file=music_filename,
            thumbnail_url=thumbnail_filename,
            duration=duration
        )

        for file_path in saved_files:
            try: os.remove(file_path)
            except: pass

        return jsonify({
            'success': True,
            'message': message,
            'video_url': output_video
        })
        
    except Exception as e:
        print(f"Error in generate_video: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get-started')
def get_started():
    if 'user_id' in session:
        if session.get('is_paid', False):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('payment'))
    else:
        return redirect(url_for('auth'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    try:
        users = get_all_users()
        videos = get_all_videos()
        total_users = len(users) if users else 0
        total_reels = len(videos) if videos else 0
        return render_template('admin.html', users=users, videos=videos,
                               total_users=total_users, total_reels=total_reels)
    except Exception as e:
        flash('Error accessing admin panel: ' + str(e))
        return redirect(url_for('index'))

if __name__ == '__main__':
    uploads_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
