vcl 4.1;

# import vmod_dynamic for better backend name resolution
import std;
import dynamic;
import directors;


# atlasfrontier-ai.cern.ch
backend backend10 {
    .host = "2001:1458:201:e5::100:c1";
    .port = "8000";
}

backend backend11 {
    .host = "2001:1458:201:e5::100:5a";
    .port = "8000";
}

backend backend12 {
    .host = "188.184.29.207";
    .port = "8000";
}


backend backend2 {
    .host = "atlasfrontier1-ai.cern.ch";
    .port = "8000";
}

backend backend3 {
    .host = "atlasfrontier2-ai.cern.ch";
    .port = "8000";
}

acl local {
 "localhost"; /* myself */
 "72.36.96.0"/24; 
 "149.165.224.0"/23; 
 "192.170.240.0"/23; 
}

sub vcl_init {
    
    # new d = dynamic.director(port = "80");

    new vdir = directors.round_robin();
    vdir.add_backend(backend10);
    vdir.add_backend(backend11);
    vdir.add_backend(backend12);
    vdir.add_backend(backend2);
    vdir.add_backend(backend3);    
}

sub vcl_recv {
    set req.backend_hint = vdir.backend();
    
    set req.http.X-frontier-id = "varnish";
    
    if (client.ip !~ local) {
        return (synth(405));
    } 

    if (req.method != "GET" && req.method != "HEAD") {
        /* We only deal with GET and HEAD by default */
        return (pipe);
    }

}
