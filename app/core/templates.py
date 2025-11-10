from fastapi.templating import Jinja2Templates


class CustomJinja2Templates(Jinja2Templates):
    """
    Кастомный Jinja2Templates с автоматическим добавлением current_user
    """
    def TemplateResponse(self, name, context=None, **kwargs):
        if context is None:
            context = {}

        request = context.get("request")
        if request:
            # Автоматически добавляем current_user из request.state
            if hasattr(request.state, "current_user"):
                context["current_user"] = request.state.current_user

            # Автоматически добавляем csrf_token
            if hasattr(request.state, "csrf_token"):
                context["csrf_token"] = request.state.csrf_token

        return super().TemplateResponse(name, context, **kwargs)


templates = CustomJinja2Templates(directory="app/templates")
