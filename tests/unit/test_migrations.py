from alembic.config import Config
from alembic.script import ScriptDirectory


def test_only_single_head_revision_in_migrations():
    config = Config()
    config.set_main_option("script_location", "alembic")
    script = ScriptDirectory.from_config(config)

    script.get_current_head()
