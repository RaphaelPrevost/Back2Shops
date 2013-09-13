from common import db_utils

class BaseResource:

    def on_get(self, req, resp, **kwargs):
        with db_utils.get_conn() as conn:
            self._on_get(req, resp, conn, **kwargs)

    def on_post(self, req, resp, **kwargs):
        with db_utils.get_conn() as conn:
            self._on_post(req, resp, conn, **kwargs)

    def _on_get(self, req, resp, conn, **kwargs):
        pass

    def _on_post(self, req, resp, conn, **kwargs):
        pass

