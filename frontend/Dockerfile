# Stage 1: Build React app
FROM node:20-alpine AS builder

WORKDIR /app

# הגדרת משתני בנייה - חשוב מאוד עבור Vite
# הגדרנו את ה-URL של ה-Backend כברירת מחדל כדי ש-Render יזהה אותו בבנייה
ARG VITE_API_URL=https://escape-room-telegram-api.onrender.com
ARG VITE_BASE_PATH=/

# הזרקת המשתנים לסביבת המערכת של ה-Container
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# העתקת קבצי הגדרות והתקנת תלויות
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# העתקת שאר קבצי הפרונטנד והרצת ה-Build
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# הגדרת שרת Nginx עבור Single Page Application (SPA)
# זה מוודא שכל נתיב בדפדפן יופנה ל-index.html
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
      try_files $uri $uri/ /index.html; \
    } \
    location /health { \
      access_log off; \
      return 200 "ok"; \
      add_header Content-Type text/plain; \
    } \
  }' > /etc/nginx/conf.d/default.conf

# העתקת התוצר המוכן מ-Stage 1 לתיקיית ההגשה של Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]