<?php

namespace App\Http\Controllers\Catalog;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Product;
use App\Models\Shop;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\View\View;

class ProductController extends Controller
{
    public function index(Request $request): View
    {
        $query = Product::public()->with(['category', 'shop']);

        if ($request->filled('q')) {
            $keyword = trim($request->input('q'));
            $query->where(function ($sub) use ($keyword) {
                $sub->where('name', 'like', "%{$keyword}%")
                    ->orWhere('description', 'like', "%{$keyword}%");
            });
        }

        if ($request->filled('category')) {
            $query->where('category_id', $request->input('category'));
        }

        if ($request->filled('shop')) {
            $query->where('shop_id', $request->input('shop'));
        }

        if ($request->filled('min_price') && is_numeric($request->input('min_price'))) {
            $query->where('price', '>=', (float) $request->input('min_price'));
        }

        if ($request->filled('max_price') && is_numeric($request->input('max_price'))) {
            $query->where('price', '<=', (float) $request->input('max_price'));
        }

        switch ($request->input('sort')) {
            case 'price_asc':
                $query->orderBy('price', 'asc');
                break;
            case 'price_desc':
                $query->orderBy('price', 'desc');
                break;
            default:
                $query->latest();
                break;
        }

        $products = $query->paginate(9)->withQueryString();
        $categories = Category::orderBy('name')->get();
        $shops = Shop::where('status', 'approved')->orderBy('name')->get();

        $wishlistIds = Auth::check()
            ? Auth::user()->wishlistProducts()->pluck('products.id')->toArray()
            : [];

        return view('catalog.products', compact(
            'products',
            'categories',
            'shops',
            'wishlistIds'
        ));
    }

    public function show(Product $product): View
    {
        $isPublic = Product::public()->whereKey($product->id)->exists();
        abort_unless($isPublic, 404);

        $product->load(['category', 'shop.user']);

        $relatedProducts = Product::public()
            ->with(['category', 'shop'])
            ->where('category_id', $product->category_id)
            ->whereKeyNot($product->id)
            ->inRandomOrder()
            ->take(4)
            ->get();

        $isWishlisted = Auth::check()
            ? Auth::user()->wishlistProducts()->whereKey($product->id)->exists()
            : false;

        $wishlistIds = Auth::check()
            ? Auth::user()->wishlistProducts()->pluck('products.id')->toArray()
            : [];

        return view('catalog.product_detail', compact(
            'product',
            'relatedProducts',
            'isWishlisted',
            'wishlistIds'
        ));
    }
}
