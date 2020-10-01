import logging

from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


def create_cas_user(tree):
    user_model = get_user_model()
    username = tree[0][0].text

    user, user_created = user_model.objects.get_or_create(username=username)

    if user_created:
        logger.info(f'Created user {user}')
    else:
        logger.info(f'User {user} has returned!')
