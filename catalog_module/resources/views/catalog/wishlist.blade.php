@extends('layouts.app')

@section('title', 'My Wishlist - Handmade Market')

@section('content')
<div class="d-flex justify-content-between align-items-center mb-4">
    <h3 class="fw-bold mb-0">My Wishlist</h3>
    <a href="{{ route('products.index') }}" class="btn btn-sm btn-outline-primary">Continue Browsing</a>
</div>

@if($products->isEmpty())
    <div class="card border-0 shadow-sm">
        <div class="card-body text-center py-5">
            <p class="text-muted mb-3">You have not saved any items to your wishlist yet.</p>
            <a href="{{ route('products.index') }}" class="btn btn-primary">Explore Catalog</a>
        </div>
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
