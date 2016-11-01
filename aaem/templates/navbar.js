

pth = window.location.pathname.split('/');
root = pth[pth.length-2] == '__web_summaries'

prefix = '../'
if (root) {
    prefix = ''
}

document.getElementById('community_drop').innerHTML = '{% for com in communities %} <li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}';

document.getElementById('region_drop').innerHTML = '{% for reg in regions %}<li class="dropdown-submenu"><a class="nested" tabindex="-1" href="#">{{ reg.region }}<span class="caret"></span></a><ul class="dropdown-menu short-menu"><li><a href="' + prefix + '{{ reg.region }}.html">Region Summary<a></li><li role="separator" class="divider"></li>{% for com in reg.communities %}<li><a href="' + prefix + '{{ com }}/overview.html">{{ com.replace("_", " ") }}</a></li>{% endfor %}</ul></li>{% endfor %}';



$(document).ready(function(){
  $('.dropdown-submenu a.nested').on("click", function(e){
    $(this).next('ul').toggle();
    e.stopPropagation();
    e.preventDefault();
  });
});


//~ $(document).ready(function(){
    //~ $('.dropdown-submenu a.nested').blur(function(){
        //~ $(this).next('ul').toggle();
    //~ });
//~ });
