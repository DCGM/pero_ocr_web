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
        query = query.join(User).filter(User.id == user_db.id)
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


def get_user_annotation_statistics(document_db=None, activity_timeout=120):
    pass









