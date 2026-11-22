@extends('layouts.app')

@section('title', 'Catalog - Handmade Market')

@section('content')
<div class="row">
    <div class="col-lg-3 mb-4">
        <div class="card shadow-sm border-0">
            <div class="card-header bg-white fw-bold">Filter Products</div>
            <div class="card-body">
                <form action="{{ route('products.index') }}" method="GET">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Keyword</label>
                        <input type="text" name="q" class="form-control form-control-sm" value="{{ request('q') }}" placeholder="Name or description...">
                    </div>

                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Category</label>
                        <select name="category" class="form-select form-select-sm">
                            <option value="">All Categories</option>
                            @foreach($categories as $category)
                                <option value="{{ $category->id }}" @selected(request('category') == $category->id)>
                                    {{ $category->name }}
                                </option>
                            @endforeach
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Artisan Shop</label>
                        <select name="shop" class="form-select form-select-sm">
                            <option value="">All Shops</option>
                            @foreach($shops as $shop)
                                <option value="{{ $shop->id }}" @selected(request('shop') == $shop->id)>
                                    {{ $shop->name }}
                                </option>
                            @endforeach
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Price Range (VND)</label>
                        <div class="row g-2">
                            <div class="col-6">
                                <input type="number" name="min_price" class="form-control form-control-sm" value="{{ request('min_price') }}" placeholder="Min">
                            </div>
                            <div class="col-6">
                                <input type="number" name="max_price" class="form-control form-control-sm" value="{{ request('max_price') }}" placeholder="Max">
                            </div>
                        </div>
                    </div>

                    <input type="hidden" name="sort" value="{{ request('sort', 'newest') }}">

                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary btn-sm">Apply Filters</button>
                        <a href="{{ route('products.index') }}" class="btn btn-outline-secondary btn-sm">Reset</a>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div class="col-lg-9">
        <div class="d-flex flex-wrap justify-content-between align-items-center bg-white p-3 rounded shadow-sm mb-3">
            <span class="text-muted small">
                Showing <strong>{{ $products->total() }}</strong> products
            </span>

            <form action="{{ route('products.index') }}" method="GET" class="d-flex align-items-center gap-2">
                @foreach(request()->except(['sort', 'page']) as $key => $val)
                    <input type="hidden" name="{{ $key }}" value="{{ $val }}">
                @endforeach
                <label class="small text-nowrap mb-0">Sort by:</label>
                <select name="sort" class="form-select form-select-sm" onchange="this.form.submit()">
                    <option value="newest" @selected(request('sort', 'newest') === 'newest')>Newest</option>
                    <option value="price_asc" @selected(request('sort') === 'price_asc')>Price: Low to High</option>
                    <option value="price_desc" @selected(request('sort') === 'price_desc')>Price: High to Low</option>
                </select>
            </form>
        </div>

        @if($products->isEmpty())
            <div class="card border-0 shadow-sm">
                <div class="card-body text-center py-5">
                    <p class="text-muted mb-2">No products matched your filter criteria.</p>
                    <a href="{{ route('products.index') }}" class="btn btn-sm btn-primary">View all products</a>
                </div>
            </div>
        @else
            <div class="row row-cols-1 row-cols-md-3 g-4">
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
    </div>
</div>
@endsection
