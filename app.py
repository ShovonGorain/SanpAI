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
import uuid
import random
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import moviepy.editor as mp
from moviepy.video.fx.all import fadein, fadeout
import numpy as np

app = Flask(__name__)

# Use environment SECRET_KEY in production. Fallback to placeholder for local dev.
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Initialize DB
init_db()

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
# Set a generous but sane file size limit (e.g., 2GB) to prevent server overload.
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

from moviepy.video.fx.all import fadein, fadeout
from moviepy.video.compositing.transitions import (
    crossfadein,
    slide_in,
    slide_out,
    fadein as comp_fadein,
    fadeout as comp_fadeout
)
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# Video Processor Class
class VideoProcessor:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.effects = ['blur', 'contrast', 'black_white', 'sepia', 'vignette', 'sharpen', 'solarize']
        self.transitions = [
            'slide_in',
            'slide_out',
            'fade',
            'crossfade',
            'scroll',
            'resize',
            'zoom_pan'
        ]
        
    def organize_images(self, image_paths):
        """Organize images by filename"""
        try:
            image_paths.sort()
        except:
            pass
        return image_paths
    
    def resize_image(self, image, max_size=(1920, 1080)):
        """Resize image to fit within max_size while maintaining aspect ratio"""
        try:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image
    
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
                # Simple vignette effect
                width, height = img.size
                pixels = img.load()
                
                for y in range(height):
                    for x in range(width):
                        dx = (x - width/2) / (width/2)
                        dy = (y - height/2) / (height/2)
                        d = (dx**2 + dy**2) ** 0.5
                        
                        r, g, b = pixels[x, y]
                        factor = 1 - d * 0.3
                        pixels[x, y] = (
                            int(r * factor),
                            int(g * factor),
                            int(b * factor)
                        )
                
                return img
            
            elif effect_name == 'sharpen':
                return img.filter(ImageFilter.SHARPEN)

            elif effect_name == 'solarize':
                return ImageOps.solarize(img)

            return img
        except Exception as e:
            print(f"Error applying effect {effect_name}: {e}")
            return image
    
    def create_video(self, image_paths, music_path, output_path):
        """Create video from images and music using CompositeVideoClip for smooth transitions."""
        try:
            organized_images = self.organize_images(image_paths)
            if not organized_images:
                return False, "No valid images found", None

            print(f"Processing {len(organized_images)} images...")

            audio_clip = None
            if music_path and os.path.exists(music_path):
                try:
                    print(f"🎵 Loading music from: {music_path}")
                    audio_clip = mp.AudioFileClip(music_path)
                    print("✅ Music loaded successfully")
                except Exception as e:
                    print(f"❌ Error loading music: {e}")

            clips = []
            standard_size = (1280, 720)
            duration_per_image = 3  # seconds

            for img_path in organized_images:
                try:
                    img = Image.open(img_path)
                    img = self.resize_image(img, standard_size)
                    
                    # Ensure image is in RGB format
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    effect = random.choice(self.effects)
                    processed_img = self.apply_effect(img, effect)
                    
                    # Convert PIL image to numpy array for moviepy
                    img_array = np.array(processed_img)

                    clip = mp.ImageClip(img_array).set_duration(duration_per_image)
                    clip = clip.set_fps(24) # Set a standard FPS

                    # Apply a zoom-pan effect to add motion
                    clip = clip.fx(mp.vfx.resize, lambda t: 1 + 0.1 * t).set_pos(('center', 'center'))
                    clips.append(clip)
                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                    continue
            
            if not clips:
                return False, "No video clips could be created from the images.", None
            
            print(f"Created {len(clips)} clips. Applying transitions...")

            transition_duration = 0.5
            video_clips = [clips[0]]

            # Use CompositeVideoClip by creating overlapping clips with transitions
            for i in range(len(clips) - 1):
                clip1 = clips[i]
                clip2 = clips[i+1]

                # Example: simple fade transition
                transition = comp_fadein(clip2, transition_duration)

                # Position the next clip to start before the previous one ends
                start_time = (i + 1) * duration_per_image - transition_duration
                video_clips.append(transition.set_start(start_time))

            final_video = CompositeVideoClip(video_clips, size=standard_size)
            total_duration = duration_per_image * len(clips) - transition_duration * (len(clips) - 1)
            final_video = final_video.set_duration(total_duration)

            if audio_clip:
                try:
                    print(f"🔊 Attaching audio. Video duration: {total_duration:.2f}s, Audio duration: {audio_clip.duration:.2f}s")
                    if audio_clip.duration < total_duration:
                        audio_clip = audio_clip.fx(mp.afx.audio_loop, duration=total_duration)
                    else:
                        audio_clip = audio_clip.subclip(0, total_duration)
                    final_video = final_video.set_audio(audio_clip)
                    print("✅ Audio attached successfully")
                except Exception as e:
                    print(f"❌ Error setting audio: {e}")
            
            print("Writing video file...")
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                threads=4
            )

            # Clean up
            final_video.close()
            if audio_clip:
                audio_clip.close()

            print("✅ Video created successfully!")

            duration = final_video.duration
            resolution = f"{final_video.size[0]}x{final_video.size[1]}"
            size = os.path.getsize(output_path) / (1024 * 1024)
            
            return True, "Video created successfully", {
                'duration': duration,
                'resolution': resolution,
                'size': size
            }
            
        except Exception as e:
            print(f"Error in create_video: {e}")
            return False, f"Video creation failed: {str(e)}", None

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
            
            # DEBUG INFORMATION
            print(f"🔍 LOGIN DEBUG - User found: {user is not None}")
            if user:
                print(f"🔍 User ID: {user['id']}")
                print(f"🔍 User Name: {user['name']}")
                print(f"🔍 Is Admin: {user['is_admin']}")
                print(f"🔍 Is Paid: {user['is_paid']}")
                print(f"🔍 Password hash: {user['password_hash'][:50]}...")
                print(f"🔍 Password provided: {password}")
            
            # DIRECT PASSWORD CHECK (no safe_check function)
            if user and check_password_hash(user['password_hash'], password):
                print("✅ PASSWORD CHECK SUCCESSFUL!")
                
                # Check if user type matches
                if (user_type == 'admin' and not user['is_admin']) or (user_type == 'user' and user['is_admin']):
                    flash('Invalid login type for this account.')
                    return render_template('auth.html')
                
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
            print(f"🔑 Creating new user with hash: {hashed[:50]}...")
            
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
        # Simulate payment processing
        plan = request.form.get('plan')
        
        # Update user payment status in database
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
    # Get user's videos from database
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
        custom_music = request.files.get('custom_music')
        
        print(f"Received {len(photos)} photos")
        
        # Validate number of photos
        if len(photos) < 5 or len(photos) > 10:
            return jsonify({
                'success': False,
                'message': 'Please select between 5 and 10 photos.'
            })

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded photos
        saved_files = []
        for photo in photos:
            if photo and photo.filename:
                # Generate a unique filename
                file_ext = os.path.splitext(photo.filename)[1].lower()
                if file_ext not in ['.jpg', '.jpeg', '.png']:
                    continue
                    
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                photo.save(save_path)
                saved_files.append(save_path)

        # Save custom music if provided
        music_filename = None
        if custom_music and custom_music.filename:
            file_ext = os.path.splitext(custom_music.filename)[1].lower()
            if file_ext in ['.mp3', '.wav']:
                music_filename = f"music_{uuid.uuid4().hex}{file_ext}"
                save_path = os.path.join(upload_dir, music_filename)
                custom_music.save(save_path)

        # Check if we have enough valid images
        if len(saved_files) < 5:
            # Clean up uploaded files
            for file_path in saved_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            if music_filename:
                try:
                    os.remove(os.path.join(upload_dir, music_filename))
                except:
                    pass
            return jsonify({
                'success': False,
                'message': 'Please select at least 5 valid images (JPG, PNG).'
            })

        # Generate a unique video filename
        video_filename = f"{uuid.uuid4().hex}.mp4"
        video_path = os.path.join(upload_dir, video_filename)
        
        print(f"Starting video creation with {len(saved_files)} images...")
        
        # Create video using our processor
        success, message, video_data = video_processor.create_video(
            saved_files,
            os.path.join(upload_dir, music_filename) if music_filename else None,
            video_path
        )
        
        if not success:
            # Clean up uploaded files
            for file_path in saved_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            if music_filename:
                try:
                    os.remove(os.path.join(upload_dir, music_filename))
                except:
                    pass
            return jsonify({
                'success': False,
                'message': message
            })
        
        # Generate thumbnail
        thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
        thumbnail_path = os.path.join(upload_dir, thumbnail_filename)
        try:
            print(f"🖼️ Generating thumbnail for video: {video_filename}")
            # Use a fresh clip object for thumbnail generation to avoid closed clip issues
            with mp.VideoFileClip(video_path) as clip:
                clip.save_frame(thumbnail_path, t=1.00) # Save frame at 1 second

            if os.path.exists(thumbnail_path):
                print(f"✅ Thumbnail generated successfully: {thumbnail_filename}")
            else:
                print("❌ Thumbnail generation failed: File not found after saving.")
                thumbnail_filename = None
        except Exception as e:
            print(f"❌ Error generating thumbnail: {e}")
            thumbnail_filename = None # Set to None if thumbnail fails

        # Add video to database with all metadata
        add_video(
            user_id=session['user_id'],
            video_url=video_filename,
            thumbnail_url=thumbnail_filename,
            title=f"Video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            music_file=music_filename,
            duration=video_data.get('duration'),
            resolution=video_data.get('resolution'),
            size=video_data.get('size')
        )

        # Clean up uploaded photos
        for file_path in saved_files:
            try:
                os.remove(file_path)
            except:
                pass

        return jsonify({
            'success': True,
            'message': message,
            'video_url': video_filename
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

# Additional routes
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