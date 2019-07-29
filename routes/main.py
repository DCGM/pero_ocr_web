# TEMPORARY CURRENT REFACTORING


@main.route('/document/<string:id>/collaborators', methods=['POST'])
@login_required
def document_edit_colaborators_post(id):
    request_form = request.form.getlist('collaborators')
    return 'Edit'


@main.route('/document/<string:id>/collaborators', methods=['GET'])
@login_required
def document_edit_colaborators_post_get(id):
    document = Document.query.get(id)
    users = User.query.all()
    users = list(filter(lambda user: user.id != document.user.id, users))
    return render_template('document/edit_collaborators.html', document=document, users=users)


