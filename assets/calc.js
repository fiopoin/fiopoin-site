(function(){
  var f=function(n){return '$'+Math.round(n).toLocaleString('en-US')};
  function calc(){
    var g=+document.getElementById('gal').value||0,d=+document.getElementById('debt').value||0,c=+document.getElementById('cash').value||0;
    var b=document.body.dataset,fuel=g*((+b.gasNow||0)-(+b.gasYearAgo||0)), intr=d*0.0025, sav=c*0.0025;
    document.getElementById('r1').textContent=f(fuel);
    document.getElementById('r2').textContent=f(intr);
    document.getElementById('r3').textContent=f(sav);
    var net=fuel*12+intr-sav;
    document.getElementById('net').textContent= net>=0
      ? 'Net effect: about '+f(net)+' a year out of your pocket'+(fuel*12>intr?', mostly from fuel.':'.')
      : 'Net effect: about '+f(-net)+' a year in your favor.';
  }
  ['gal','debt','cash'].forEach(function(id){document.getElementById(id).addEventListener('input',calc)});
  calc();
  document.getElementById('sf').addEventListener('submit',function(e){e.preventDefault();document.getElementById('sn').textContent='Email signup is opening soon. A new edition is posted here every morning.'});
})();
(function(){
  document.querySelectorAll('.card figure img').forEach(function(img){
    function fail(){img.closest('figure').classList.add('noimg')}
    if(img.complete&&img.naturalWidth===0){fail()}else{img.addEventListener('error',fail)}
  });
})();
