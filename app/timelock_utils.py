import flask

def render_template(tmpl_name, **kwargs):
    return flask.render_template(tmpl_name, **kwargs)