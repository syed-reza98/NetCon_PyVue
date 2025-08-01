FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Install Quasar CLI
RUN npm install -g @quasar/cli

# Copy source code
COPY . .

# Expose the port
EXPOSE 8080

# Set environment variables
ENV NODE_ENV=development

# Start the development server
CMD ["npm", "run", "dev"]