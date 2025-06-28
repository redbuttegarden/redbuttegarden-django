import json
import subprocess
import sys


def update_zappa_settings(env):
    # Load the existing zappa_settings.json file
    with open('../zappa_settings.json', 'r') as f:
        zappa_settings = json.load(f)

    # Get the Terraform outputs for the specified environment
    terraform_output = subprocess.check_output([
        'terraform', 'output', '-json',
    ], env={"AWS_PROFILE": "terraform"}, text=True)
    terraform_output = json.loads(terraform_output)

    # Update the corresponding section in zappa_settings.json
    zappa_settings[env]['vpc_config']['SubnetIds'] = terraform_output['private_subnet_ids']['value']
    zappa_settings[env]['vpc_config']['SecurityGroupIds'] = [terraform_output['security_group_id']['value']]
    zappa_settings[env]['environment_variables']['DB_HOST'] = \
        terraform_output['db_instance_endpoint']['value'].split(':')[0]
    zappa_settings[env]['environment_variables']['CLOUDFRONT_DISTRIBUTION_ID'] = \
        terraform_output['cloudfront_distribution_id']['value']
    zappa_settings[env]['environment_variables']['CLOUDFRONT_DOMAIN_NAME'] = \
        terraform_output['cloudfront_domain_name']['value']
    zappa_settings[env]['environment_variables']['LAMBDA_ENDPOINT_URL'] = \
        terraform_output['lambda_endpoint_url']['value']

    # Save the updated zappa_settings.json file
    with open('../zappa_settings.json', 'w') as f:
        json.dump(zappa_settings, f, indent=4)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_zappa_vpc.py <environment>")
        sys.exit(1)

    environment = sys.argv[1]
    update_zappa_settings(environment)
