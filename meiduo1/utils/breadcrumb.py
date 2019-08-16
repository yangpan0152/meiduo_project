def get_breadcrumb(cat3):
    cat1 = cat3.parent.parent
    breadcrumb = {
        'cat1': {
            'name': cat1.name,
            'url': cat1.chl_level1.all()[0].url
        },
        'cat2': cat3.parent,
        'cat3': cat3
    }

    return breadcrumb