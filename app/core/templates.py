from fastapi.templating import Jinja2Templates


class CustomJinja2Templates(Jinja2Templates):
    """
    Кастомный Jinja2Templates с автоматическим добавлением current_user
    """
    def TemplateResponse(self, name, context=None, **kwargs):
        if context is None:
            context = {}

        # Автоматически добавляем current_user из request.state
        request = context.get("request")
        if request and hasattr(request.state, "current_user"):
            context["current_user"] = request.state.current_user

        return super().TemplateResponse(name, context, **kwargs)


templates = CustomJinja2Templates(directory="app/templates")
