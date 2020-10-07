from app import db_session
from app.db import Document, Image, TextLine, Annotation, User, TextRegion
from collections import defaultdict
from Levenshtein import distance


def filter_document(query, document_db):
    if document_db is not None:
        query = query.join(Document).filter(Document.id == document_db.id)
    return query


def filter_user(query, user_db):
    if user_db is not None:
        query = query.filter(Annotation.user_id == user_db.id)
    return query


def get_document_annotation_statistics(document_db=None, activity_timeout=120):
    user_lines = defaultdict(set)
    user_changed_lines = defaultdict(set)
    user_times = defaultdict(list)
    user_changed_chars = defaultdict(int)

    annotations = db_session.query(Annotation).join(TextLine).join(TextRegion).join(Image)
    annotations = filter_document(annotations, document_db)
    for annotation_db in annotations:
        user_id = annotation_db.user_id
        user_times[user_id].append(annotation_db.created_date)
        user_lines[user_id].add(annotation_db.text_line_id)
        if annotation_db.text_original != annotation_db.text_edited:
            user_changed_lines[user_id].add(annotation_db.text_line_id)
            user_changed_chars[user_id] += distance(annotation_db.text_edited, annotation_db.text_original)

    total_lines = set()
    total_changed_lines = set()
    total_changed_chars = 0
    for user_id in user_lines:
        total_lines |= user_lines[user_id]
        total_changed_lines |= user_changed_lines[user_id]
        total_changed_chars += user_changed_chars[user_id]
    total_lines = len(total_lines)
    total_changed_lines = len(total_changed_lines)

    user_lines = {user_id: len(user_lines[user_id]) for user_id in user_lines}
    user_changed_lines = {user_id: len(user_changed_lines[user_id]) for user_id in user_changed_lines}

    total_characters = 0
    used_ids = set()
    user_chars = defaultdict(int)
    for user_id in user_lines:
        user_texts = db_session.query(TextLine.id, TextLine.text).join(Annotation).join(TextRegion).join(Image).distinct()
        user_texts = filter_document(user_texts, document_db).filter(Annotation.user_id == user_id)
        for id, text in user_texts:
            user_chars[user_id] += len(text)
            if id not in used_ids:
                total_characters += len(text)
                used_ids.add(id)

    total_activity_time = 0
    for user_id in user_times:
        times = sorted(user_times[user_id])
        last_t = times[0]
        user_activity_duration = 0
        for t in times[1:]:
            delta = (t - last_t).total_seconds()
            if delta < activity_timeout:
                user_activity_duration += delta
            last_t = t
        user_times[user_id] = user_activity_duration
        total_activity_time += user_activity_duration

    all_stats = []
    for user_id in user_lines:
        user_db = User.query.get(user_id)
        all_stats.append({
            'user': f'{user_db.first_name} {user_db.last_name}',
            'lines': user_lines[user_id],
            'changed_lines': user_changed_lines[user_id],
            'characters': user_chars[user_id],
            'changed_characters': user_changed_chars[user_id],
            'time': f'{user_times[user_id] / 3600:0.1f}'
        })

    all_stats.append({
        'user': 'TOTAL',
        'lines': total_lines,
        'changed_lines': total_changed_lines,
        'characters': total_characters,
        'changed_characters': total_changed_chars,
        'time': f'{total_activity_time / 3600:0.1f}'
    })

    return all_stats


def get_user_annotation_statistics(user_db=None, activity_timeout=120):
    document_lines = defaultdict(set)
    document_changed_lines = defaultdict(set)
    document_times = defaultdict(list)
    document_changed_chars = defaultdict(int)

    annotated_documents = db_session.query(Document).join(Image).join(TextRegion).join(TextLine).join(Annotation)
    annotated_documents = filter_user(annotated_documents, user_db).distinct().all()

    for document_db in annotated_documents:
        document_id = document_db.id
        annotations = db_session.query(Annotation).join(TextLine).join(TextRegion).join(Image)
        annotations = filter_user(annotations, user_db)
        annotations = filter_document(annotations, document_db)
        for annotation_db in annotations:
            document_times[document_id].append(annotation_db.created_date)
            document_lines[document_id].add(annotation_db.text_line_id)
            if annotation_db.text_original != annotation_db.text_edited:
                document_changed_lines[document_id].add(annotation_db.text_line_id)
                document_changed_chars[document_id] += distance(annotation_db.text_edited, annotation_db.text_original)

    total_lines = set()
    total_changed_lines = set()
    total_changed_chars = 0
    for document_id in document_lines:
        total_lines |= document_lines[document_id]
        total_changed_lines |= document_changed_lines[document_id]
        total_changed_chars += document_changed_chars[document_id]
    total_lines = len(total_lines)
    total_changed_lines = len(total_changed_lines)

    document_lines = {document_id: len(document_lines[document_id]) for document_id in document_lines}
    document_changed_lines = {document_id: len(document_changed_lines[document_id]) for document_id in document_changed_lines}


    total_characters = 0
    used_ids = set()
    document_chars = defaultdict(int)
    for document_id in document_lines:
        document_texts = db_session.query(TextLine.id, TextLine.text).join(Annotation).join(TextRegion).join(
            Image).join(Document).filter(Document.id == document_id).distinct()
        document_texts = filter_user(document_texts, user_db)
        for id, text in document_texts:
            l = len(text)
            document_chars[document_id] += l
            if id not in used_ids:
                total_characters += l
                used_ids.add(id)

    total_activity_time = 0
    for document_id in document_times:
        times = sorted(document_times[document_id])
        last_t = times[0]
        document_activity_duration = 0
        for t in times[1:]:
            delta = (t - last_t).total_seconds()
            if delta < activity_timeout:
                document_activity_duration += delta
            last_t = t
        document_times[document_id] = document_activity_duration
        total_activity_time += document_activity_duration

    all_stats = []
    for document_id in document_lines:
        document_db = Document.query.get(document_id)
        all_stats.append({
            'user': document_db.name,
            'lines': document_lines[document_id],
            'changed_lines': document_changed_lines[document_id],
            'characters': document_chars[document_id],
            'changed_characters': document_changed_chars[document_id],
            'time': f'{document_times[document_id] / 3600:0.1f}'
        })

    all_stats.append({
        'user': 'TOTAL',
        'lines': total_lines,
        'changed_lines': total_changed_lines,
        'characters': total_characters,
        'changed_characters': total_changed_chars,
        'time': f'{total_activity_time / 3600:0.1f}'
    })

    return all_stats






