<html>
<head>
  <title>Open Issues Summary</title>
  <style>
    body {
      margin: 1.5em 3em;
    }
    li {
      margin-bottom: 0.15em;
    }
    .label { 
      font-family: sans-serif;
      display: inline;
    	padding: .15em .5em .25em;
      margin-left: .4em;
    	font-size: 65%;
    	font-weight: 700;
    	line-height: 1;
    	color: #fff;
    	text-align: center;
    	white-space: nowrap;
    	vertical-align: baseline;
    	border-radius: .25em;
    }
  </style>
</head>
<body>
  <h1>Open Issues Summary</h1>
  {% for repo in repos %}
  <h2><a href="https://github.com/{{ repo.id }}">{{ repo.name }}</a></h2>
    {% for issue in repo.issues %}
      <li>
        <a href="{{ issue.html_url }}">#{{ issue.number }}</a> - {{ issue.title }}
        (<em>open {{ issue.open_for }} days</em>)
        {% for label in issue.labels %}
          <span class="label" style="background-color: #{{ label.color }}; color: #{{ label.text_color }}">{{ label.name }}</span> 
        {% endfor %}</li>
      </li>
    {% endfor %}
  {% endfor %}
</body>
</html>