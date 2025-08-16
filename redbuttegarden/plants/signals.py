from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import BloomEvent

@receiver(m2m_changed, sender=BloomEvent.collections.through)
def update_title_on_collections_change(sender, instance, action, **kwargs):
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f'm2m_changed triggered for BloomEvent {instance.pk}, action={action}')

    if action in ['post_add', 'post_remove', 'post_clear']:
        logger.debug(f'Checking title update for BloomEvent {instance.pk}')
        if not instance.title and not instance.species:
            species_names = set(
                collection.species.full_name for collection in instance.collections.all()
            )
            logger.debug(f'Species names from collections: {species_names}')
            if len(species_names) == 1:
                new_title = f'Bloom Event for {species_names.pop()}'
            else:
                new_title = 'Bloom Event for Multiple Species'

            logger.debug(f'Updating title to: {new_title}')
            instance.title = new_title
            instance.save(update_fields=['title'])
