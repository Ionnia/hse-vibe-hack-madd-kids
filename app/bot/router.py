from aiogram import Router

from app.bot.handlers import ask, cancel, help, progress, review, start, study, topics, upload

main_router = Router(name="main")

# Register all sub-routers
main_router.include_router(cancel.router)  # Must be first — works in any state
main_router.include_router(start.router)
main_router.include_router(help.router)
main_router.include_router(study.router)
main_router.include_router(review.router)
main_router.include_router(topics.router)
main_router.include_router(progress.router)
main_router.include_router(ask.router)
main_router.include_router(upload.router)  # Must be last (catches text messages)
