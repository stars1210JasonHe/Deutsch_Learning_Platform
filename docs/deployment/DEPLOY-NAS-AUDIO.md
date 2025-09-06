# NAS Deployment with German Audio Integration

This guide shows how to deploy Vibe Deutsch on your Synology NAS with full access to your German audio library.

## Overview

Your setup:
- **Audio Location**: `\\DS420plus\homes\德语学习` (965 MP3 files)
- **Deployment Target**: Same NAS (DS420plus)
- **Audio Access**: Direct local file serving (no network latency)

## Deployment Steps

### 1. Prepare Audio Directory

On your Synology NAS, ensure audio files are accessible:
```bash
# Your audio structure should be:
/volume1/homes/德语学习/
├── Klett Linie1 A2/
├── Klett Linie1 B1/  
├── L-i-1-A-1/
│   └── Linie 1/
│       └── audios/
│           └── Kapitel 1 bis Kapitel 8/
│               ├── 1-01.mp3
│               ├── 1-02.mp3
│               └── ...
└── all_vocab.json
```

### 2. Build Docker Image

```bash
# Build the image
docker build -t vibe-deutsch .
```

### 3. Run with Audio Volume Mount

```bash
# Run container with audio directory mounted
docker run -d \
  --name vibe-deutsch \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /volume1/docker/vibe-deutsch/data:/app/data \
  -v "/volume1/homes/德语学习":/app/audio \
  -e AUDIO_PATH="/app/audio" \
  -e DATABASE_URL="sqlite:///./data/app.db" \
  -e OPENAI_API_KEY="your_openai_key" \
  -e OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
  -e SECRET_KEY="your_secret_key" \
  vibe-deutsch
```

### 4. Synology Container Manager Setup

**Via Container Manager GUI:**

1. **Image**: `vibe-deutsch` (built locally)
2. **Port Settings**: 
   - Local Port: `8000` → Container Port: `8000`
3. **Volume Mounts**:
   - `/volume1/docker/vibe-deutsch/data` → `/app/data`
   - `/volume1/homes/德语学习` → `/app/audio`
4. **Environment Variables**:
   ```
   AUDIO_PATH=/app/audio
   DATABASE_URL=sqlite:///./data/app.db
   OPENAI_API_KEY=your_openai_key_here
   SECRET_KEY=your_secret_key_here
   ```

## Audio System Usage

### 1. Build Audio Index

After deployment, build the audio index:

```bash
# API call to scan all audio files
curl -X POST "http://your-nas-ip:8000/audio/rebuild-index" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Browse Audio Library

- **View all courses**: `GET /audio/courses`
- **Course details**: `GET /audio/courses/L-i-1-A-1`
- **Chapter audio**: `GET /audio/courses/L-i-1-A-1/chapters/1`
- **Search audio**: `POST /audio/search` with `{"query": "01"}`

### 3. Play Audio Files

- **Stream audio**: `GET /audio/play/{file_id}`
- **Download audio**: `GET /audio/download/{file_id}`
- **File info**: `GET /audio/info/{file_id}`

### 4. Audio Statistics

```bash
curl "http://your-nas-ip:8000/audio/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Example response:
```json
{
  "total_files": 965,
  "total_courses": 3,
  "total_size_mb": 2840.5,
  "courses": {
    "L-i-1-A-1": 320,
    "Klett Linie1 A2": 322,
    "Klett Linie1 B1": 323
  }
}
```

## Frontend Integration

The frontend will automatically detect available audio files and provide:

- **Course browser** with audio playback
- **Lesson-by-lesson audio navigation**
- **Search functionality** across all audio files
- **Integrated audio player** with progress tracking

## File Structure After Mount

Inside the container:
```
/app/
├── audio/                    # Mounted from /volume1/homes/德语学习
│   ├── L-i-1-A-1/           # → 965 MP3 files accessible
│   ├── Klett Linie1 A2/
│   └── Klett Linie1 B1/
├── data/
│   ├── app.db               # SQLite database
│   └── audio_index.json     # Audio file index
└── app/                     # Application code
```

## Benefits of This Setup

✅ **Zero Network Latency** - Audio files served locally  
✅ **No Storage Duplication** - Direct access to existing files  
✅ **Fast Startup** - No file copying required  
✅ **Automatic Discovery** - Scans all courses and lessons  
✅ **Scalable** - Works with thousands of audio files  
✅ **Efficient** - Minimal resource usage on NAS  

## Audio API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /audio/rebuild-index` | Scan and index all audio files |
| `GET /audio/stats` | Get library statistics |
| `GET /audio/courses` | List all courses |
| `GET /audio/courses/{name}` | Get course audio files |
| `GET /audio/courses/{name}/chapters/{n}` | Get chapter audio |
| `POST /audio/search` | Search audio files |
| `GET /audio/play/{file_id}` | Stream audio file |
| `GET /audio/download/{file_id}` | Download audio file |
| `GET /audio/info/{file_id}` | Get file information |

## Troubleshooting

### Audio Files Not Found
- Check volume mount: `/volume1/homes/德语学习` → `/app/audio`
- Verify AUDIO_PATH environment variable: `/app/audio`
- Rebuild index: `POST /audio/rebuild-index`

### Permission Issues
```bash
# On NAS, ensure container can read audio files
chmod -R 755 /volume1/homes/德语学习
```

### Network Access
- Ensure port 8000 is open on NAS firewall
- Access via: `http://your-nas-ip:8000`

This setup gives you a complete German learning platform with access to all 965 audio files directly on your NAS!