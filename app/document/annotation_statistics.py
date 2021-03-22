from app import db_session, engine
from app.db import Document, Image, TextLine, Annotation, User, TextRegion
from collections import defaultdict
from Levenshtein import distance
from sqlalchemy.sql import select, and_
from sqlalchemy import func


def filter_document(query, document_db):
    if document_db is not None:
        query = query.join(Document).filter(Document.id == document_db.id)
    return query


def fill_stats():
    print('query')
    annotations = db_session.query(Annotation).filter(Annotation.character_change_count == None)
    print('start')
    for annotation_db in annotations:
        annotation_db.character_change_count = distance(annotation_db.text_edited, annotation_db.text_original)
        annotation_db.character_count = len(annotation_db.text_edited)
    print('commit')
    db_session.commit()
    print('done')


def filter_user(query, user_db):
    if user_db is not None:
        query = query.filter(Annotation.user_id == user_db.id)
    return query


def get_document_annotation_statistics_by_day(document_id):
    annotations = db_session.query(func.DATE(Annotation.created_date), User.first_name, User.last_name, func.count(Annotation.created_date))\
        .join(TextLine).join(TextRegion).join(Image).join(User).filter(Image.document_id == document_id)\
        .group_by(func.DATE(Annotation.created_date), User.id)

    return annotations.all()


def compute_statistics(results, activity_timeout):
    user_lines = defaultdict(set)
    user_changed_lines = defaultdict(set)
    user_times = defaultdict(list)
    user_changed_chars = defaultdict(int)
    line_lengths = dict()

    for user_id, text_line_id, created_date, character_change_count, character_count in results:
        user_id = user_id
        user_times[user_id].append(created_date)
        user_lines[user_id].add(text_line_id)
        line_lengths[text_line_id] = character_count
        if character_change_count != 0:
            user_changed_lines[user_id].add(text_line_id)
            user_changed_chars[user_id] += character_change_count

    total_characters = sum(line_lengths.values())
    user_chars = dict()
    for user_id in user_lines:
        user_chars[user_id] = sum([line_lengths[line_id] for line_id in user_lines[user_id]])

    total_lines = len(line_lengths)
    total_changed_lines = set()
    total_changed_chars = 0
    for user_id in user_lines:
        total_changed_lines |= user_changed_lines[user_id]
        total_changed_chars += user_changed_chars[user_id]
    total_changed_lines = len(total_changed_lines)

    user_lines = {user_id: len(user_lines[user_id]) for user_id in user_lines}
    user_changed_lines = {user_id: len(user_changed_lines[user_id]) for user_id in user_changed_lines}

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

    return user_lines, user_changed_lines, user_chars, user_changed_chars, user_times, total_lines, total_changed_lines, total_characters, total_changed_chars, total_activity_time


def get_document_annotation_statistics(document_db=None, activity_timeout=120):
    with engine.connect() as conn:
        sel = select([Annotation.user_id, Annotation.text_line_id, Annotation.created_date, Annotation.character_change_count, Annotation.character_count])
        if document_db:
            sel = sel.where(and_(
                Annotation.text_line_id == TextLine.id,
                TextLine.region_id == TextRegion.id,
                TextRegion.image_id == Image.id,
                Image.document_id == document_db.id))
        results = conn.execute(sel)
        user_lines, user_changed_lines, user_chars, user_changed_chars, user_times, total_lines, total_changed_lines, total_characters, total_changed_chars, total_activity_time = \
            compute_statistics(results, activity_timeout)

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
    with engine.connect() as conn:
        sel = select([Document.id, Annotation.text_line_id, Annotation.created_date, Annotation.character_change_count, Annotation.character_count])
        if user_db:
            sel = sel.where(and_(
                Annotation.text_line_id == TextLine.id,
                TextLine.region_id == TextRegion.id,
                TextRegion.image_id == Image.id,
                Image.document_id == Document.id,
                Annotation.user_id == user_db.id))
        else:
            sel = sel.where(and_(
                Annotation.text_line_id == TextLine.id,
                TextLine.region_id == TextRegion.id,
                TextRegion.image_id == Image.id,
                Image.document_id == Document.id))
        results = conn.execute(sel)

        document_lines, document_changed_lines, document_chars, document_changed_chars, document_times, total_lines, total_changed_lines, total_characters, total_changed_chars, total_activity_time = \
            compute_statistics(results, activity_timeout)

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
