function template_set_url_callback(element){
    return new Promise((resolve, reject) => {
        element.onload = () => resolve();
        element.onerror = reject;
        element.src = element.dataset.src;
    });
}

let max_concurrent = 2;
let active_elements = [];
let global_lazy_list = [];
let lazy_callback__ = null;

function activate_element(element, imageObserver){
    imageObserver.unobserve(element);
    global_lazy_list = global_lazy_list.filter(x => x != element);
    active_elements.push(element);
}

async function add_lazy(element, imageObserver){
    if(active_elements.length < max_concurrent){
        activate_element(element, imageObserver);
        await lazy_callback__(element).catch((e) => null);
        let index = active_elements.indexOf(element);
        if(index > -1) {
            active_elements.splice(index, 1);
        }

        while(global_lazy_list.length > 0){
            element = global_lazy_list.pop();
            activate_element(element, imageObserver);
            await lazy_callback__(element).catch((e) => null);
            let index = active_elements.indexOf(element);
            if(index > -1) {
                active_elements.splice(index, 1);
            }
        }
    } else {
        global_lazy_list.push(element)
    }
}

function cancel_lazy(element){
    global_lazy_list = global_lazy_list.filter(x => x != element)
}


function manage_lazy_images(lazy_callback) {
    var lazyloadImages;
    lazy_callback__ = lazy_callback;

    if ("IntersectionObserver" in window) {
        lazyloadImages = document.querySelectorAll(".lazy-img");
        var imageObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    add_lazy(entry.target, imageObserver);
                } else {
                    cancel_lazy(entry.target)
               }
            });
        });

        lazyloadImages.forEach(function (image) {
            imageObserver.observe(image);
        });
    } else {
        var lazyloadThrottleTimeout;
        lazyloadImages = document.querySelectorAll(".lazy-img");

        function lazyload() {
            if (lazyloadThrottleTimeout) {
                clearTimeout(lazyloadThrottleTimeout);
            }

            lazyloadThrottleTimeout = setTimeout(function () {
                var scrollTop = window.pageYOffset;
                lazyloadImages.forEach(function (img) {
                    if (img.offsetTop < (window.innerHeight + scrollTop)) {
                        lazy_callback__(img);
                        img.classList.remove('lazy-img');
                    }
                });
                if (lazyloadImages.length == 0) {
                    document.removeEventListener("scroll", lazyload);
                    window.removeEventListener("resize", lazyload);
                    window.removeEventListener("orientationChange", lazyload);
                }
            }, 20);
        }

        document.addEventListener("scroll", lazyload);
        window.addEventListener("resize", lazyload);
        window.addEventListener("orientationChange", lazyload);
    }
}



