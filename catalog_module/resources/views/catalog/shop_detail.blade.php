@extends('layouts.app')

@section('title', $shop->name . ' - Artisan Shop')

@section('content')
<div class="card border-0 shadow-sm mb-4">
    <div class="card-body p-4">
        <div class="row align-items-center">
            <div class="col-md-8">
                <span class="badge bg-success mb-2">Verified Artisan Shop</span>
                <h2 class="fw-bold mb-1">{{ $shop->name }}</h2>
                @if($shop->user)
                    <p class="small text-muted mb-2">Artisan: <strong>{{ $shop->user->name }}</strong></p>
                @endif
                <p class="text-secondary mb-0">{{ $shop->description ?? 'No shop description provided.' }}</p>
            </div>
            <div class="col-md-4 text-md-end mt-3 mt-md-0">
                <div class="p-3 bg-light rounded d-inline-block text-center">
                    <div class="fs-4 fw-bold text-primary">{{ $totalProducts }}</div>
                    <div class="small text-muted">Listed Products</div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="d-flex justify-content-between align-items-center mb-3">
    <h4 class="fw-bold mb-0">Shop Catalog</h4>
    <form action="{{ route('shops.show', $shop) }}" method="GET" class="d-flex align-items-center gap-2">
        <label class="small text-nowrap mb-0">Sort by:</label>
        <select name="sort" class="form-select form-select-sm" onchange="this.form.submit()">
            <option value="newest" @selected(request('sort', 'newest') === 'newest')>Newest</option>
            <option value="price_asc" @selected(request('sort') === 'price_asc')>Price: Low to High</option>
            <option value="price_desc" @selected(request('sort') === 'price_desc')>Price: High to Low</option>
        </select>
    </form>
</div>

@if($products->isEmpty())
    <div class="alert alert-light border text-center py-4">
        This shop has not listed any products yet.
    </div>
@else
    <div class="row row-cols-1 row-cols-sm-2 row-cols-md-4 g-4">
        @foreach($products as $product)
            <div class="col">
                @include('catalog.partials.product_card', ['product' => $product, 'wishlistIds' => $wishlistIds])
            </div>
        @endforeach
    </div>

    <div class="mt-4 d-flex justify-content-center">
        {{ $products->links('pagination::bootstrap-5') }}
    </div>
@endif
@endsection
