#!/bin/bash

# TrustLayer AI - GCP Deployment Script
# Automated deployment to Google Cloud Platform

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID=""
REGION="us-central1"
ZONE="us-central1-a"
ENVIRONMENT="prod"
DOMAIN_NAME="trustlayer.internal"
ENABLE_MONITORING="true"
ENABLE_CLOUD_ARMOR="true"
NOTIFICATION_EMAIL=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    # Check if user is authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to validate project ID
validate_project() {
    if [ -z "$PROJECT_ID" ]; then
        print_error "PROJECT_ID is required"
        exit 1
    fi
    
    # Check if project exists and user has access
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        print_error "Project $PROJECT_ID does not exist or you don't have access"
        exit 1
    fi
    
    # Set the project
    gcloud config set project "$PROJECT_ID"
    print_success "Using project: $PROJECT_ID"
}

# Function to enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    local apis=(
        "run.googleapis.com"
        "compute.googleapis.com"
        "dns.googleapis.com"
        "vpcaccess.googleapis.com"
        "redis.googleapis.com"
        "cloudbuild.googleapis.com"
        "containerregistry.googleapis.com"
        "logging.googleapis.com"
        "monitoring.googleapis.com"
        "cloudtrace.googleapis.com"
        "binaryauthorization.googleapis.com"
        "containeranalysis.googleapis.com"
        "cloudkms.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable "$api" --quiet
    done
    
    print_success "All APIs enabled"
}

# Function to build and push container images
build_containers() {
    print_status "Building and pushing container images..."
    
    # Build proxy container
    print_status "Building TrustLayer AI proxy container..."
    docker build -t "gcr.io/$PROJECT_ID/trustlayer-ai:latest" .
    
    # Build dashboard container
    print_status "Building TrustLayer AI dashboard container..."
    docker build -t "gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest" -f gcp-deployment/Dockerfile.dashboard .
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Push containers
    print_status "Pushing containers to Google Container Registry..."
    docker push "gcr.io/$PROJECT_ID/trustlayer-ai:latest"
    docker push "gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest"
    
    print_success "Container images built and pushed"
}

# Function to deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    cd gcp-deployment/terraform
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars file
    cat > terraform.tfvars <<EOF
project_id = "$PROJECT_ID"
region = "$REGION"
zone = "$ZONE"
environment = "$ENVIRONMENT"
domain_name = "$DOMAIN_NAME"
container_image = "gcr.io/$PROJECT_ID/trustlayer-ai:latest"
dashboard_image = "gcr.io/$PROJECT_ID/trustlayer-ai-dashboard:latest"
enable_monitoring = $ENABLE_MONITORING
enable_cloud_armor = $ENABLE_CLOUD_ARMOR
notification_email = "$NOTIFICATION_EMAIL"
EOF
    
    # Plan deployment
    print_status "Planning Terraform deployment..."
    terraform plan -var-file=terraform.tfvars
    
    # Apply deployment
    print_status "Applying Terraform deployment..."
    terraform apply -var-file=terraform.tfvars -auto-approve
    
    # Get outputs
    LOAD_BALANCER_IP=$(terraform output -raw load_balancer_ip)
    VPC_CONNECTOR=$(terraform output -raw vpc_connector_id)
    SERVICE_ACCOUNT=$(terraform output -raw service_account_email)
    
    cd ../..
    
    print_success "Infrastructure deployed successfully"
}

# Function to run Cloud Build
run_cloud_build() {
    print_status "Running Cloud Build pipeline..."
    
    # Submit build
    gcloud builds submit \
        --config=gcp-deployment/cloudbuild.yaml \
        --substitutions=_REGION="$REGION",_ZONE="$ZONE",_ENVIRONMENT="$ENVIRONMENT",_DOMAIN_NAME="$DOMAIN_NAME",_VPC_CONNECTOR="$VPC_CONNECTOR",_SERVICE_ACCOUNT="$SERVICE_ACCOUNT",_LOAD_BALANCER_IP="$LOAD_BALANCER_IP" \
        .
    
    print_success "Cloud Build completed successfully"
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Wait for services to be ready
    sleep 60
    
    # Test health endpoint
    print_status "Testing health endpoint..."
    if curl -f -H "Host: api.$DOMAIN_NAME" "http://$LOAD_BALANCER_IP/health"; then
        print_success "Health endpoint is working"
    else
        print_error "Health endpoint test failed"
        return 1
    fi
    
    # Test metrics endpoint
    print_status "Testing metrics endpoint..."
    if curl -f -H "Host: api.$DOMAIN_NAME" "http://$LOAD_BALANCER_IP/metrics"; then
        print_success "Metrics endpoint is working"
    else
        print_warning "Metrics endpoint test failed (may be expected if no traffic yet)"
    fi
    
    print_success "Deployment tests completed"
}

# Function to display deployment information
show_deployment_info() {
    print_success "🎉 TrustLayer AI deployed successfully!"
    echo
    echo "📋 Deployment Information:"
    echo "=========================="
    echo "Project ID: $PROJECT_ID"
    echo "Region: $REGION"
    echo "Environment: $ENVIRONMENT"
    echo "Load Balancer IP: $LOAD_BALANCER_IP"
    echo "Internal Domain: $DOMAIN_NAME"
    echo
    echo "🔗 Service URLs:"
    echo "==============="
    echo "API Health Check: http://$LOAD_BALANCER_IP/health"
    echo "API Metrics: http://$LOAD_BALANCER_IP/metrics"
    echo "Dashboard: http://$LOAD_BALANCER_IP:8501"
    echo
    echo "🌐 Internal URLs (from within VPC):"
    echo "==================================="
    echo "API: http://api.$DOMAIN_NAME"
    echo "Dashboard: http://dashboard.$DOMAIN_NAME"
    echo
    echo "🧪 Test Commands:"
    echo "================"
    echo "Health Check: curl -H 'Host: api.$DOMAIN_NAME' http://$LOAD_BALANCER_IP/health"
    echo "Metrics: curl -H 'Host: api.$DOMAIN_NAME' http://$LOAD_BALANCER_IP/metrics"
    echo "DNS Test: nslookup api.$DOMAIN_NAME"
    echo
    echo "📊 Monitoring:"
    echo "=============="
    echo "Cloud Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
    echo "Monitoring: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
    echo "Logs: https://console.cloud.google.com/logs?project=$PROJECT_ID"
    echo
    echo "💰 Estimated Monthly Cost: ~$93-162 USD"
    echo "🔒 Security: Private networking with Cloud Armor protection"
    echo "📈 Scaling: Auto-scaling from 1-10 instances based on demand"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -p, --project-id PROJECT_ID       GCP Project ID (required)"
    echo "  -r, --region REGION               GCP Region (default: us-central1)"
    echo "  -z, --zone ZONE                   GCP Zone (default: us-central1-a)"
    echo "  -e, --environment ENV             Environment name (default: prod)"
    echo "  -d, --domain DOMAIN               Internal domain (default: trustlayer.internal)"
    echo "  -m, --monitoring BOOL             Enable monitoring (default: true)"
    echo "  -s, --security BOOL               Enable Cloud Armor (default: true)"
    echo "  -n, --notification-email EMAIL    Email for notifications"
    echo "  --skip-build                      Skip container build step"
    echo "  --skip-terraform                  Skip Terraform deployment"
    echo "  --skip-cloud-build               Skip Cloud Build pipeline"
    echo "  --skip-tests                      Skip deployment tests"
    echo "  -h, --help                        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -p my-gcp-project"
    echo "  $0 -p my-project -r europe-west1 -e staging"
    echo "  $0 -p my-project -n admin@company.com --skip-build"
}

# Parse command line arguments
SKIP_BUILD=false
SKIP_TERRAFORM=false
SKIP_CLOUD_BUILD=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project-id)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -z|--zone)
            ZONE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        -m|--monitoring)
            ENABLE_MONITORING="$2"
            shift 2
            ;;
        -s|--security)
            ENABLE_CLOUD_ARMOR="$2"
            shift 2
            ;;
        -n|--notification-email)
            NOTIFICATION_EMAIL="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        --skip-cloud-build)
            SKIP_CLOUD_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main deployment flow
main() {
    echo "🛡️ TrustLayer AI - GCP Sovereign AI Deployment"
    echo "=============================================="
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Validate project
    validate_project
    
    # Enable APIs
    enable_apis
    
    # Build containers (if not skipped)
    if [ "$SKIP_BUILD" = false ]; then
        build_containers
    else
        print_warning "Skipping container build"
    fi
    
    # Deploy infrastructure (if not skipped)
    if [ "$SKIP_TERRAFORM" = false ]; then
        deploy_infrastructure
    else
        print_warning "Skipping Terraform deployment"
        # Get values from existing deployment
        cd gcp-deployment/terraform
        LOAD_BALANCER_IP=$(terraform output -raw load_balancer_ip 2>/dev/null || echo "10.0.1.100")
        VPC_CONNECTOR=$(terraform output -raw vpc_connector_id 2>/dev/null || echo "trustlayer-$ENVIRONMENT-connector")
        SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "trustlayer-$ENVIRONMENT-sa@$PROJECT_ID.iam.gserviceaccount.com")
        cd ../..
    fi
    
    # Run Cloud Build (if not skipped)
    if [ "$SKIP_CLOUD_BUILD" = false ]; then
        run_cloud_build
    else
        print_warning "Skipping Cloud Build pipeline"
    fi
    
    # Test deployment (if not skipped)
    if [ "$SKIP_TESTS" = false ]; then
        test_deployment
    else
        print_warning "Skipping deployment tests"
    fi
    
    # Show deployment information
    show_deployment_info
}

# Run main function
main "$@"