---
layout: default
title: Home
---
<div class="tag-filters">
  {% assign tags = site.posts | map: "tags" | join: "," | split: "," | uniq %}
  {% for tag in tags %}
    {% if tag != "" %}<span class="tag-pill">{{ tag }}</span>{% endif %}
  {% endfor %}
</div>

{% for post in site.posts %}
<div class="post-card">
  <a class="title" href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a>
  <div class="post-meta">
    <span>{{ post.date | date: "%b %d, %Y" }}</span>
    <span class="read-time">{{ post.read_time }}</span>
    {% if post.tags %}<span>{{ post.tags | join: " · " }}</span>{% endif %}
  </div>
</div>
{% endfor %}
