from flask import session
from app.services.sars_service import SARSService


def register_context_processors(app):
    """Register global template context processors."""

    @app.context_processor
    def inject_sars_config():
        company_id = session.get('selected_company_id')
        if company_id:
            sars_config = SARSService.get_company_sars_config(company_id)
        else:
            sars_config = SARSService.get_global_sars_config().to_dict()
        return {'sars_config': sars_config}


