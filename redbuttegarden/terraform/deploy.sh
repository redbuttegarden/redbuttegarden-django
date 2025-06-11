#!/bin/bash
set -e

ENV=$1
ACTION=$2

if [ "$ACTION" == "up" ]; then
  terraform init
  AWS_PROFILE=terraform terraform apply -var-file=terraform_${ENV}.tfvars -auto-approve
  python3 update_zappa_vpc.py $ENV
elif [ "$ACTION" == "down" ]; then
  AWS_PROFILE=terraform terraform destroy -var-file=terraform_${ENV}.tfvars -auto-approve
else
  echo "Usage: ./deploy.sh [environment] [up|down]"
fi
