# 5MB Media Converter

A serverless web application that automatically compresses images and videos to under 5 megabytes, designed specifically for school apps and platforms with file size restrictions.

## 🚀 Features

- **Automatic Compression**: Upload any image or video and get it compressed to under 5MB
- **Smart Processing**: Uses FFmpeg for optimal video compression and image optimization
- **Modern UI**: Beautiful, responsive interface with drag-and-drop support
- **Real-time Progress**: Live upload progress and processing status updates
- **Serverless Architecture**: Built on AWS Lambda for scalability and cost-efficiency
- **Large File Support**: Handles files up to 100MB using multipart uploads
- **No Conversion Needed**: Files already under 5MB are returned immediately

## 🛠️ Technology Stack

- **Frontend**: Vanilla JavaScript with modern CSS
- **Backend**: Python 3.11 on AWS Lambda
- **Media Processing**: FFmpeg static binaries
- **Storage**: AWS S3 with multipart upload support
- **Infrastructure**: Serverless Framework for deployment
- **Testing**: Automated test suite with synthetic media generation

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js and npm (for Serverless Framework)
- Python 3.11+
- FFmpeg and FFprobe (for local testing)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Serverless Framework
npm install -g serverless

# Install Python dependencies (if running tests)
pip install -r tests/requirements.txt
```

### 2. Configure AWS

```bash
# Configure AWS credentials
aws configure
```

### 3. Deploy

```bash
# Deploy to AWS
./deploy.sh
```

The deployment script will:
- Create the S3 bucket for file storage
- Deploy the Lambda functions
- Set up API Gateway endpoints
- Configure S3 event triggers

### 4. Access Your Application

After deployment, you'll get an API Gateway URL. Visit it in your browser to start using the converter.

## 📁 Project Structure

```
├── handler.py              # Main web app and API endpoints
├── converter.py            # Media processing Lambda function
├── serverless.yml          # Serverless Framework configuration
├── deploy.sh              # Deployment script
├── deploy-html.sh         # HTML-only deployment script
├── tail_converter.sh      # Log monitoring script
├── layer/                 # FFmpeg binaries for Lambda
│   └── bin/
│       ├── ffmpeg
│       └── ffprobe
└── tests/                 # Automated testing suite
    ├── generate_and_upload.py
    ├── requirements.txt
    └── README.md
```

## 🔧 API Endpoints

- `GET /` - Web application interface
- `POST /api/multipart/initiate` - Start multipart upload
- `GET /api/multipart/url` - Get presigned URL for upload part
- `POST /api/multipart/complete` - Complete multipart upload
- `GET /api/status` - Check processing status

## 🧪 Testing

The project includes a comprehensive test suite that generates synthetic media files and tests the entire upload/conversion pipeline:

```bash
# Set your deployed API base URL
export API_BASE="https://your-api-gateway-url.amazonaws.com"

# Run the test suite
python tests/generate_and_upload.py
```

The test suite will:
- Generate various image and video files up to 200MB
- Upload them through the API
- Monitor processing completion
- Generate a detailed JSON report

## 📊 How It Works

1. **Upload**: Files are uploaded using S3 multipart upload for reliability
2. **Trigger**: S3 events automatically trigger the converter Lambda function
3. **Processing**: 
   - Images are compressed using FFmpeg with optimized JPEG settings
   - Videos are re-encoded with H.264 and optimized bitrates
4. **Storage**: Processed files are stored in S3 with presigned download URLs
5. **Delivery**: Users get a download link for the compressed file

## ⚙️ Configuration

### Environment Variables

- `BUCKET_NAME`: S3 bucket for file storage (auto-configured)

### Lambda Configuration

- **Web App**: 512MB RAM, 30s timeout
- **Converter**: 10GB RAM, 15min timeout, 10GB ephemeral storage

## 🔍 Monitoring

Monitor converter function logs:

```bash
./tail_converter.sh
```

## 📝 File Size Limits

- **Input**: Up to 100MB (larger files typically won't compress well to 5MB)
- **Output**: Always under 5MB
- **Processing**: Files already under 5MB are returned immediately

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the test suite results for debugging information
2. Monitor Lambda logs using the provided scripts
3. Ensure your AWS permissions are correctly configured

---

Built with ❤️ for students and educators dealing with file size restrictions.
