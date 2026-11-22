@extends('layouts.app')

@section('title', $product->name . ' - Handmade Market')

@section('content')
@php
    $thumb = $product->thumbnail ?? $product->image ?? null;
    $imageUrl = $thumb
        ? (str_starts_with($thumb, 'http') ? $thumb : asset('storage/' . $thumb))
        : 'https://placehold.co/600x450?text=Handmade+Art';
@endphp

<nav aria-label="breadcrumb" class="mb-3">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{{ route('home') }}">Home</a></li>
        <li class="breadcrumb-item"><a href="{{ route('products.index') }}">Catalog</a></li>
        @if($product->category)
            <li class="breadcrumb-item">
                <a href="{{ route('products.index', ['category' => $product->category_id]) }}">
                    {{ $product->category->name }}
                </a>
            </li>
        @endif
        <li class="breadcrumb-item active" aria-current="page">{{ $product->name }}</li>
    </ol>
</nav>

<div class="card border-0 shadow-sm mb-5">
    <div class="row g-0">
        <div class="col-md-5">
            <img src="{{ $imageUrl }}" class="img-fluid rounded-start w-100 h-100" style="object-fit: cover; max-height: 450px;" alt="{{ $product->name }}">
        </div>
        <div class="col-md-7">
            <div class="card-body p-4">
                @if($product->category)
                    <span class="badge bg-secondary mb-2">{{ $product->category->name }}</span>
                @endif

                <h2 class="fw-bold">{{ $product->name }}</h2>
                <h3 class="text-danger fw-bold my-3">{{ number_format($product->price, 0, ',', '.') }} VND</h3>

                @if(isset($product->stock))
                    <p class="small text-muted">
                        Availability:
                        @if($product->stock > 0)
                            <span class="text-success fw-semibold">In Stock ({{ $product->stock }} available)</span>
                        @else
                            <span class="text-danger fw-semibold">Out of Stock</span>
                        @endif
                    </p>
                @endif

                <div class="mb-4">
                    <h6 class="fw-bold">Description</h6>
                    <p class="text-secondary mb-0">{!! nl2br(e($product->description)) !!}</p>
                </div>

                @if($product->shop)
                    <div class="p-3 bg-light rounded border mb-4 d-flex justify-content-between align-items-center">
                        <div>
                            <div class="small text-muted">Crafted by</div>
                            <a href="{{ route('shops.show', $product->shop) }}" class="fw-bold text-decoration-none fs-6">
                                {{ $product->shop->name }}
                            </a>
                        </div>
                        <a href="{{ route('shops.show', $product->shop) }}" class="btn btn-sm btn-outline-dark">
                            Visit Shop
                        </a>
                    </div>
                @endif

                <div class="d-flex flex-wrap gap-2">
                    @if(Route::has('cart.add'))
                        <form action="{{ route('cart.add', $product) }}" method="POST" class="d-flex gap-2">
                            @csrf
                            <input type="number" name="quantity" value="1" min="1" max="{{ $product->stock ?? 99 }}" class="form-control" style="width: 80px;">
                            <button type="submit" class="btn btn-success" @disabled(($product->stock ?? 1) <= 0)>
                                <i class="bi bi-cart-plus"></i> Add to Cart
                            </button>
                        </form>
                    @endif

                    @auth
                        @if(auth()->user()->role === 'buyer')
                            <form action="{{ route('wishlist.toggle', $product) }}" method="POST">
                                @csrf
                                <button type="submit" class="btn {{ $isWishlisted ? 'btn-danger' : 'btn-outline-danger' }}">
                                    <i class="bi {{ $isWishlisted ? 'bi-heart-fill' : 'bi-heart' }}"></i>
                                    {{ $isWishlisted ? 'Saved in Wishlist' : 'Add to Wishlist' }}
                                </button>
                            </form>
                        @endif
                    @else
                        <a href="{{ route('login') }}" class="btn btn-outline-danger">
                            <i class="bi bi-heart"></i> Add to Wishlist
                        </a>
                    @endauth
                </div>
            </div>
        </div>
    </div>
</div>

@if($relatedProducts->isNotEmpty())
<section>
    <h4 class="fw-bold mb-3">Related Products</h4>
    <div class="row row-cols-1 row-cols-sm-2 row-cols-md-4 g-4">
        @foreach($relatedProducts as $related)
            <div class="col">
                @include('catalog.partials.product_card', ['product' => $related, 'wishlistIds' => $wishlistIds])
            </div>
        @endforeach
    </div>
</section>
@endif
@endsection
