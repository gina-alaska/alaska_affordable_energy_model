

pth = window.location.pathname.split('/');
root = pth[pth.length-2] == '__web_summaries'

prefix = '../'
if (root) {
    prefix = ''
}

document.getElementById('community_drop').innerHTML = '{% for com in communities %} <li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}';


