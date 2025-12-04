# 🚀 CI/CD AI Optimizer

AI-Powered CI/CD Pipeline Optimizer with Infrastructure Monitoring

## 🎯 Features

- 🤖 AI-powered build failure prediction
- ⏱️ Build duration estimation
- 📊 Real-time infrastructure monitoring
- 📈 Beautiful Grafana dashboards
- 🔄 CircleCI integration
- 🐳 Fully Dockerized

## 🚀 Quick Start

1. Clone the repository
2. Copy `.env.example` to `.env` and add your CircleCI credentials
3. Run setup: `./infrastructure/scripts/setup.sh`
4. Start services: `docker-compose up -d`
5. Access dashboards:
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - API Docs: http://localhost:8000/docs

## 📚 Documentation

See individual component READMEs for detailed documentation.

## 🛠️ Tech Stack

- Backend: FastAPI, Python
- ML: Scikit-learn, PyTorch
- Database: MongoDB
- Monitoring: Prometheus, Grafana
- CI/CD: CircleCI, Bazel
- Infrastructure: Docker, Kubernetes
