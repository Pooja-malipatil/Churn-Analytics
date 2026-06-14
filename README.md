# 🤖 ChurnAI — AI-Powered Customer Churn Prediction & Retention Analytics Platform

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![React](https://img.shields.io/badge/React-18-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.3-orange)

A full-stack AI analytics platform that predicts customer churn, identifies churn causes, generates retention strategies, and displays business analytics dashboards — all with explainable AI.

---

## 🚀 Live Demo

- **Frontend:** https://your-vercel-url.vercel.app
- **Backend API:** https://your-railway-url.railway.app
- **API Docs:** https://your-railway-url.railway.app/docs

---

## ✨ Features

### 🔮 AI Prediction
- Churn probability scoring (0-100%)
- Random Forest + Logistic Regression models
- SHAP explainability — know WHY a customer will churn
- Risk categorization (Low / Medium / High / Critical)

### 📊 Analytics Dashboard
- Real-time churn insights from any dataset
- Churn by contract type, tenure, internet service
- Financial impact analysis (revenue at risk)
- Service impact comparison charts

### 🎯 Retention Intelligence
- AI-generated retention strategies per customer
- At-risk customer priority queue
- Action buttons (Call / Email / Send Offer)
- Prediction history tracking

### 📁 Universal Dataset Support
- Upload ANY CSV churn dataset
- Auto-detection of column names
- User only selects the churn column
- Machine auto-maps everything else
- Model retraining on new data

### 📄 PDF Reports
- Full analytics PDF report
- Individual customer prediction report
- SHAP factor analysis included
- Downloadable from the UI

### 🔐 Authentication
- JWT-based login and registration
- Protected routes
- Password hashing with PBKDF2

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18 | UI Framework |
| Vite | Build Tool |
| Tailwind CSS v4 | Styling |
| React Router v6 | Navigation |
| Axios | HTTP Client |
| Recharts | Data Visualization |
| Lucide React | Icons |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API Framework |
| Uvicorn | ASGI Server |
| SQLAlchemy | ORM |
| PostgreSQL | Database |
| Pydantic | Validation |
| python-jose | JWT Auth |
| ReportLab | PDF Generation |

### Machine Learning
| Technology | Purpose |
|------------|---------|
| Scikit-learn | ML Models |
| Pandas | Data Processing |
| NumPy | Numerical Computing |
| SHAP | Model Explainability |
| Joblib | Model Persistence |

---

## 📁 Project Structure

```
churn-analytics/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # DB connection
│   │   ├── routers/             # API routes
│   │   │   ├── predict.py       # Prediction endpoints
│   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   ├── retention.py     # Retention endpoints
│   │   │   ├── upload.py        # Dataset upload
│   │   │   ├── customers.py     # Customer history
│   │   │   ├── auth.py          # Authentication
│   │   │   └── reports.py       # PDF reports
│   │   ├── services/            # Business logic
│   │   │   ├── ml_service.py    # ML prediction service
│   │   │   ├── auth_service.py  # Auth logic
│   │   │   └── pdf_service.py   # PDF generation
│   │   ├── models/              # Database models
│   │   │   ├── customer.py
│   │   │   ├── prediction.py
│   │   │   └── user.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── prediction.py
│   │   │   └── auth.py
│   │   └── ml/                  # ML pipeline
│   │       └── train.py         # Training script
│   ├── data/                    # Datasets
│   ├── models_saved/            # Trained models
│   ├── requirements.txt
│   └── Procfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── PredictCustomer.jsx
│   │   │   ├── Analytics.jsx
│   │   │   ├── RetentionCenter.jsx
│   │   │   ├── UploadDataset.jsx
│   │   │   ├── Customers.jsx
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── components/
│   │   │   └── layout/
│   │   │       └── Layout.jsx
│   │   ├── context/
│   │   │   ├── AuthContext.jsx
│   │   │   └── DataContext.jsx
│   │   └── services/
│   │       └── api.js
│   └── package.json
│
└── README.md
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Pooja-malipatil/Churn-Analytics.git
cd Churn-Analytics/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "DATABASE_URL=postgresql://postgres:password@localhost:5432/churn_db" > .env
echo "DEBUG=True" >> .env

# Create database
psql -U postgres -c "CREATE DATABASE churn_db;"

# Train the model (download Kaggle dataset first)
python -m app.ml.train

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 🤖 Training the Model

Download the [Kaggle Telco Customer Churn dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) and place it in `backend/data/`.

```bash
cd backend
python -m app.ml.train
```

**Model Performance (Kaggle Telco Dataset):**
| Metric | Random Forest | Logistic Regression |
|--------|--------------|---------------------|
| Accuracy | 76.2% | 74.0% |
| Precision | 53.6% | 50.6% |
| Recall | 78.6% | 79.9% |
| F1 Score | 63.7% | 62.0% |
| **ROC-AUC** | **0.846** | **0.841** |

---

## 📡 API Endpoints

### Authentication
```
POST /api/v1/auth/register    Register new user
POST /api/v1/auth/login       Login and get JWT token
GET  /api/v1/auth/me          Get current user
```

### Prediction
```
POST /api/v1/predict          Predict single customer churn
POST /api/v1/predict/batch    Batch prediction
GET  /api/v1/predict/history/{id}  Customer prediction history
```

### Analytics
```
GET /api/v1/analytics/summary           Dashboard summary stats
GET /api/v1/analytics/churn-by-contract Contract analysis
GET /api/v1/analytics/churn-by-tenure   Tenure analysis
GET /api/v1/analytics/churn-by-internet Internet service analysis
GET /api/v1/analytics/churn-by-payment  Payment method analysis
GET /api/v1/analytics/churn-by-charges  Charges analysis
GET /api/v1/analytics/service-impact    Service impact analysis
GET /api/v1/analytics/at-risk-customers At-risk customers list
GET /api/v1/analytics/model-features    Model feature definitions
```

### Dataset Upload
```
POST /api/v1/upload/dataset    Upload CSV dataset
POST /api/v1/upload/train      Start model retraining
GET  /api/v1/upload/status     Training progress
GET  /api/v1/upload/dataset/info  Active dataset info
```

### Reports
```
GET  /api/v1/reports/analytics    Download analytics PDF
POST /api/v1/reports/customer     Download customer PDF
```

### Customers
```
GET    /api/v1/customers/predictions           All predictions
GET    /api/v1/customers/predictions/{id}      Customer history
GET    /api/v1/customers/stats                 Prediction statistics
DELETE /api/v1/customers/predictions/{id}      Delete prediction
```

---

## 🌍 Deployment

### Backend → Railway
1. Connect GitHub repo to Railway
2. Set Root Directory to `backend`
3. Add PostgreSQL database
4. Set environment variables
5. Deploy

### Frontend → Vercel
1. Connect GitHub repo to Vercel
2. Set Root Directory to `frontend`
3. Add `VITE_API_URL` environment variable
4. Deploy

---

## 🧠 How It Works

```
1. User uploads CSV dataset
2. System auto-detects column names
3. User selects the churn column
4. Random Forest + Logistic Regression trained
5. SHAP explainer built
6. Best model deployed automatically
7. All pages update with new dataset data
8. User can predict churn for any new customer
9. AI generates retention strategies
10. PDF reports downloadable
```

---

## 📸 Screenshots

### Dashboard
Real-time churn metrics and charts from active dataset.

### Predict Churn
AI-powered prediction with SHAP explainability and retention strategies.

### Analytics
4-tab analysis — Overview, Contract, Services, Financial.

### Retention Center
At-risk customers ranked by churn probability with action buttons.

### Upload Dataset
3-step upload — Upload CSV → Select churn column → Train model.

### Customer History
Full prediction history per customer with trend analysis.

---

## 👩‍💻 Author

**Pooja Malipatil**
- GitHub: [@Pooja-malipatil](https://github.com/Pooja-malipatil)

---

## 📝 License

This project is for educational and portfolio purposes.

---

## 🙏 Dataset Credit

[IBM Telco Customer Churn Dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) via Kaggle
