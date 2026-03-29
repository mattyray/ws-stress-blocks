FROM node:22-slim

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

CMD ["npx", "vite", "dev", "--host"]
