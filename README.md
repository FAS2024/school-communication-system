# School Communication System (COMS)

A modern, secure and centralized school communication platform built with Django. Designed to eliminate paper-based memos and streamline communication across multiple school branches among administrators, teachers, non-teaching staff, students, and parents.

---

## 📌 Project Description

School Communication System (COMS) is a robust internal messaging platform for schools with multiple branches. It enables seamless digital communication between staff, students, and parents. Admins can manage users and monitor communication effectively. External users (like parents) can submit enquiries and be onboarded after approval.

---

## ✨ Features

- Multi-branch communication
- Role-based access (Super Admin, Branch Admin, Teaching Staff, etc.)
- Internal messaging (e.g. memos, announcements)
- Enquiry system for non-authenticated users
- Secure authentication and authorization
- Admin control for user creation and approval
- Responsive frontend (Bootstrap 5 Admin UI)

---

## 🏗️ Tech Stack

- **Backend:** Django 4.x
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript (no SPA framework)
- **Database:** MySQL
- **Auth:** Django Custom User Model
- **Deployment:** To be deployed (Heroku/Vercel/Render/Hostinger/etc.)

---

## 📁 Folder Structure (Simplified)

coms/
├── core/ # Main Django app
│ ├── templates/
│ ├── static/
│ ├── models/
│ ├── views.py
│ └── urls.py
├── accounts/ # CustomUser, authentication
│ ├── models.py
│ ├── forms.py
│ ├── views.py
├── media/ # Uploaded files
├── static/ # Custom JS/CSS
├── templates/ # Main HTML templates
├── manage.py
└── requirements.txt

yaml
Copy
Edit

---

## ⚙️ Setup Instructions

```bash
# Clone the project
git clone https://github.com/your-username/school-communication-system.git
cd school-communication-system

# Set up virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure .env and database (MySQL)
# Create MySQL DB and update settings.py

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
🔐 Roles & Permissions
Role	Can Send Message	Can Manage Users	Can View Enquiries	Branch Scope
Super Admin	✅	✅	✅	All Branches
Branch Admin	✅	✅ (Own Branch)	✅	Own Branch
Teaching Staff	✅	❌	❌	Own Branch
Non-teaching	✅	❌	❌	Own Branch
Student	✅	❌	❌	Own Branch
Parent	✅	❌	❌	Own Branch
Visitor	❌	❌	Submit Enquiry	—

📷 Screenshots
Add screenshots of UI here later (login page, dashboard, inbox, etc.)

🚀 Demo Link
🔗 Live Demo (To be added after deployment)

👤 Author
Backend Developer: [Your Name]
Email: your.email@example.com
GitHub: github.com/your-username

📄 License
This project is licensed under the MIT License.
Feel free to use and contribute!

🔐 Security Notice
All credentials and sensitive data should be stored in .env and never committed to version control.
A .gitignore file is included for security best practices.