// Small auth helper for attaching JWT
window.Auth = (function(){
  function getToken(){ try { return localStorage.getItem('jwt') || ''; } catch(e){ return ''; } }
  function setToken(t){ try { localStorage.setItem('jwt', t); } catch(e){} }
  function clear(){ try { localStorage.removeItem('jwt'); } catch(e){} }

  async function authFetch(url, opts={}){
    const token = getToken();
    const headers = Object.assign({}, opts.headers || {}, token ? { 'Authorization': `Bearer ${token}` } : {});
    const res = await fetch(url, Object.assign({}, opts, { headers }));
    return res;
  }

  async function json(res){
    try { return await res.clone().json(); }
    catch(_) { return { error: await res.text() }; }
  }

  return { getToken, setToken, clear, fetch: authFetch, json };
})();
