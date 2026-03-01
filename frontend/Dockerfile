# Stage 1: Build React app
FROM node:20-alpine AS builder

WORKDIR /app

# משתני בנייה עבור Vite
ARG VITE_API_URL=https://escape-room-telegram-api.onrender.com
ARG VITE_BASE_PATH=/

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

# העתקה מהנתיב הנוכחי (בהנחה שאנחנו בתוך תיקיית הפרונטנד)
COPY package.json package-lock.json* ./
RUN npm install

# העתקת כל שאר הקבצים
COPY . ./
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# הגדרת Nginx ל-SPA
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

# העתקת קבצי ה-dist מהשלב הקודם
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]