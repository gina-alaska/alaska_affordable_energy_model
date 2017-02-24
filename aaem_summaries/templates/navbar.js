

pth = window.location.pathname.split('/');
root = pth[pth.length-2] == '__web_summaries'

prefix = '../'
if (root) {
    prefix = ''
}

document.getElementById('community_drop').innerHTML = '{% for com in communities %} <li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}';

document.getElementById('region_drop').innerHTML = '{% for reg in regions %}<li class="dropdown-submenu"><a class="nested" tabindex="-1" href="#">{{ reg.region }}<span class="caret"></span></a><ul class="dropdown-menu short-menu"><li><a href="' + prefix + '{{ reg.clean }}.html">Region Summary<a></li><li role="separator" class="divider"></li>{% for com in reg.communities %}<li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}</ul></li>{% endfor %}';

document.getElementById('senate_drop').innerHTML = '{% for reg in senate_dist %}<li class="dropdown-submenu"><a class="nested" tabindex="-1" href="#">{{ reg.district }}<span class="caret"></span></a><ul class="dropdown-menu short-menu">{% for com in reg.communities %}<li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}</ul></li>{% endfor %}';

document.getElementById('house_drop').innerHTML = '{% for reg in house_dist %}<li class="dropdown-submenu"><a class="nested" tabindex="-1" href="#">{{ reg.district }}<span class="caret"></span></a><ul class="dropdown-menu short-menu"><li>{% for com in reg.communities %}<li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}</ul></li>{% endfor %}';

document.getElementById('tech_drop').innerHTML = '{% for reg in techs %}<li class="dropdown-submenu"><a class="nested" tabindex="-1" href="#">{{ reg.district }}<span class="caret"></span></a><ul class="dropdown-menu short-menu"><li><a href="' + prefix + '{{ reg.clean }}.html">Summary<a></li><li role="separator" class="divider"></li><li><small>Viable Communities</small></li>{% for com in reg.communities %}<li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}</ul></li>{% endfor %}';


$(document).ready(function(){
  $(document).on('click', '.dropdown-submenu a.nested', function(e) {
    $(this).next('ul').toggle();
    
    var parentLi = $(this).parent();
    var parentUl = parentLi.parent();
    var activeLi = parentUl.find('.active');
    
    if (activeLi.length > 0) {
        activeLi.find('ul').toggle();
        activeLi.removeClass('active');
    }
    $(parentLi).addClass('active');
    e.stopPropagation();
    e.preventDefault();
  });
});
