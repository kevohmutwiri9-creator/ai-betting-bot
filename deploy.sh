#!/bin/bash

# AI Betting Bot Deployment Script
# This script automates the deployment process

set -e  # Exit on any error

echo "🎯 AI Betting Bot Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Check environment variables
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check for required environment variables
    required_vars=("TELEGRAM_BOT_TOKEN" "API_SECRET_KEY" "SESSION_SECRET_KEY")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=YOUR_" .env || grep -q "^${var}=your-" .env; then
            print_warning "Environment variable $var is not set or using placeholder value"
        fi
    done
    
    print_status "Environment file checked"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs data ssl
    chmod 755 logs data ssl
}

# Generate SSL certificates (self-signed for development)
generate_ssl() {
    if [ ! -f "ssl/cert.pem" ]; then
        print_status "Generating self-signed SSL certificates..."
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        chmod 600 ssl/key.pem
        chmod 644 ssl/cert.pem
    else
        print_status "SSL certificates already exist"
    fi
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Build the main application
    docker-compose build betting-bot
    
    # Start core services
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Start the main application
    docker-compose up -d betting-bot nginx
    
    print_status "Services deployed successfully"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec betting-bot python -c "
from data_collector import FootballDataCollector
collector = FootballDataCollector()
print('Database initialized successfully')
"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_status "✅ Application is healthy and responding"
    else
        print_error "❌ Health check failed"
        exit 1
    fi
}

# Show deployment info
show_info() {
    print_status "Deployment completed successfully!"
    echo ""
    echo "🌐 Web Dashboard: https://localhost"
    echo "📊 API Documentation: https://localhost/api"
    echo "📝 Logs: docker-compose logs -f betting-bot"
    echo ""
    echo "🔧 Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart: docker-compose restart"
    echo "  Update: git pull && docker-compose build && docker-compose up -d"
    echo ""
    print_warning "Note: Using self-signed SSL certificates. Your browser will show a warning."
}

# Main deployment function
main() {
    print_status "Starting deployment process..."
    
    check_docker
    check_env
    create_directories
    generate_ssl
    deploy_services
    run_migrations
    health_check
    show_info
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        print_status "Stopping all services..."
        docker-compose down
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "update")
        print_status "Updating application..."
        git pull
        docker-compose build
        docker-compose up -d
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and images. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            docker-compose down -v --rmi all
            docker system prune -f
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|update|clean}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy the application (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs"
        echo "  update  - Update and redeploy"
        echo "  clean   - Remove everything (destructive)"
        exit 1
        ;;
esac
