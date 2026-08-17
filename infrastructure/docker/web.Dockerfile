FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install deps
RUN npm ci 2>/dev/null || npm install

# Copy source
COPY . .

# Build Next.js (production)
RUN npm run build

CMD ["npm", "run", "dev", "--", "-p", "3000"]
