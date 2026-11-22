<?php

namespace App\Http\Controllers\Catalog;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\Http\RedirectResponse;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class WishlistController extends Controller
{
    public function index(): View
    {
        $products = Auth::user()
            ->wishlistProducts()
            ->with(['category', 'shop'])
            ->latest('wishlists.created_at')
            ->paginate(12);

        $wishlistIds = $products->pluck('id')->toArray();

        return view('catalog.wishlist', compact('products', 'wishlistIds'));
    }

    public function toggle(Product $product): RedirectResponse
    {
        $isPublic = Product::public()->whereKey($product->id)->exists();
        abort_unless($isPublic, 404);

        $result = Auth::user()->wishlistProducts()->toggle($product->id);
        $added = count($result['attached']) > 0;

        $message = $added
            ? 'Added product to your wishlist.'
            : 'Removed product from your wishlist.';

        return back()->with('success', $message);
    }
}
