FROM node:20-alpine

WORKDIR /app

ENV VITE_HOST=0.0.0.0 \
    VITE_PORT=5173 \
    CHOKIDAR_USEPOLLING=true

COPY package*.json ./
RUN npm install || npm install --legacy-peer-deps

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
