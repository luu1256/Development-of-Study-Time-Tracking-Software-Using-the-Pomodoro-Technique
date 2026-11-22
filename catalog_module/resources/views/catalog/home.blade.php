@extends('layouts.app')

@section('title', 'Home - Handmade Market')

@section('content')
<div class="p-4 p-md-5 mb-4 rounded-3 bg-dark text-white">
    <div class="col-lg-8">
        <h1 class="display-6 fw-bold">Authentic Handmade & Art Creations</h1>
        <p class="lead my-3">Discover one-of-a-kind works crafted by dedicated independent artisans.</p>
        <form action="{{ route('products.index') }}" method="GET" class="d-flex gap-2 mt-4" style="max-width: 520px;">
            <input type="text" name="q" class="form-control" placeholder="Search ceramics, woodwork, paintings...">
            <button type="submit" class="btn btn-warning fw-semibold text-nowrap">Search</button>
        </form>
    </div>
</div>

@if($categories->isNotEmpty())
<section class="mb-5">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="fw-bold mb-0">Browse Categories</h4>
        <a href="{{ route('products.index') }}" class="text-decoration-none">View all</a>
    </div>
    <div class="d-flex flex-wrap gap-2">
        @foreach($categories as $category)
            <a href="{{ route('products.index', ['category' => $category->id]) }}" class="btn btn-outline-dark">
                {{ $category->name }}
            </a>
        @endforeach
    </div>
</section>
@endif

<section class="mb-5">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h4 class="fw-bold mb-0">Latest Arrivals</h4>
        <a href="{{ route('products.index') }}" class="btn btn-sm btn-outline-primary">Explore Catalog</a>
    </div>

    @if($featuredProducts->isEmpty())
        <div class="alert alert-light border text-center">No products are currently available.</div>
    @else
        <div class="row row-cols-1 row-cols-sm-2 row-cols-md-4 g-4">
            @foreach($featuredProducts as $product)
                <div class="col">
                    @include('catalog.partials.product_card', ['product' => $product, 'wishlistIds' => $wishlistIds])
                </div>
            @endforeach
        </div>
    @endif
</section>

@if($featuredShops->isNotEmpty())
<section class="mb-4">
    <h4 class="fw-bold mb-3">Featured Artisan Shops</h4>
    <div class="row row-cols-1 row-cols-md-4 g-4">
        @foreach($featuredShops as $shop)
            <div class="col">
                <div class="card h-100 shadow-sm border-0">
                    <div class="card-body">
                        <h6 class="fw-bold mb-1">
                            <a href="{{ route('shops.show', $shop) }}" class="text-decoration-none text-dark">
                                {{ $shop->name }}
                            </a>
                        </h6>
                        <p class="small text-muted mb-2">{{ Str::limit($shop->description, 80) }}</p>
                        <span class="badge bg-secondary">{{ $shop->products_count }} items</span>
                    </div>
                    <div class="card-footer bg-white border-top-0">
                        <a href="{{ route('shops.show', $shop) }}" class="btn btn-sm btn-outline-dark w-100">Visit Shop</a>
                    </div>
                </div>
            </div>
        @endforeach
    </div>
</section>
@endif
@endsection
