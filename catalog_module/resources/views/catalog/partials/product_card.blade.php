@php
    $inWishlist = in_array($product->id, $wishlistIds ?? []);
    $thumb = $product->thumbnail ?? $product->image ?? null;
    $imageUrl = $thumb
        ? (str_starts_with($thumb, 'http') ? $thumb : asset('storage/' . $thumb))
        : 'https://placehold.co/400x300?text=Handmade+Art';
@endphp

<div class="card h-100 shadow-sm border-0">
    <a href="{{ route('products.show', $product) }}" class="text-decoration-none">
        <img src="{{ $imageUrl }}" class="card-img-top" alt="{{ $product->name }}" style="height: 210px; object-fit: cover;">
    </a>
    <div class="card-body d-flex flex-column">
        @if($product->category)
            <span class="badge bg-light text-dark border align-self-start mb-2">
                {{ $product->category->name }}
            </span>
        @endif

        <h6 class="card-title mb-1">
            <a href="{{ route('products.show', $product) }}" class="text-decoration-none text-dark fw-semibold">
                {{ $product->name }}
            </a>
        </h6>

        @if($product->shop)
            <p class="small text-muted mb-2">
                Artisan:
                <a href="{{ route('shops.show', $product->shop) }}" class="text-decoration-none">
                    {{ $product->shop->name }}
                </a>
            </p>
        @endif

        <div class="mt-auto pt-2">
            <span class="text-danger fw-bold fs-5">
                {{ number_format($product->price, 0, ',', '.') }} VND
            </span>
        </div>
    </div>

    <div class="card-footer bg-white border-top-0 d-flex justify-content-between align-items-center pb-3">
        <a href="{{ route('products.show', $product) }}" class="btn btn-sm btn-outline-primary">
            Details
        </a>

        @auth
            @if(auth()->user()->role === 'buyer')
                <form action="{{ route('wishlist.toggle', $product) }}" method="POST" class="m-0">
                    @csrf
                    <button type="submit" class="btn btn-sm {{ $inWishlist ? 'btn-danger' : 'btn-outline-danger' }}">
                        <i class="bi {{ $inWishlist ? 'bi-heart-fill' : 'bi-heart' }}"></i>
                    </button>
                </form>
            @endif
        @else
            <a href="{{ route('login') }}" class="btn btn-sm btn-outline-danger" title="Sign in to save items">
                <i class="bi bi-heart"></i>
            </a>
        @endauth
    </div>
</div>
