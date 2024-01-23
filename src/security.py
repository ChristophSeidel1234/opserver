import secure

def secure_headers():
    hsts = secure.StrictTransportSecurity().max_age(31536000).include_subdomains()
    cache = secure.CacheControl().no_cache().no_store().must_revalidate()
    referrer = secure.ReferrerPolicy().strict_origin_when_cross_origin()
    xxss = secure.XXSSProtection().set("1; mode=block")
    csp = (secure.ContentSecurityPolicy()
            .default_src("'none'")
            .script_src("'self'") 
            .style_src("'self' 'nonce-G3xdDzNndUUu4'")
            .frame_src("'none'")
            .font_src("'self'")
            .form_action("'none'")
            .frame_ancestors("'none'")
            .object_src("'none'")
            .base_uri("'none'"))
    return secure.Secure(hsts=hsts, cache=cache, referrer=referrer, csp=csp, xxp=xxss)
    