from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid


def index(request):
    categories = Category.objects.all()
    activeListings = Listing.objects.filter(isActive = True)
    return render(request, "auctions/index.html", {
        "listings": activeListings,
        "categories": categories
    })

def listing(request, id):
    listingData = Listing.objects.get(pk = id)
    userIsInWatch = request.user in listingData.watchlist.all()
    comments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing":listingData,
        "userIsInWatch":userIsInWatch,
        "comments":comments,
        "isOwner":isOwner
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    return HttpResponseRedirect(reverse("listing", args=(id,)))


def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    actualUser = request.user
    listingData.watchlist.remove(actualUser)
    return HttpResponseRedirect(reverse("listing", args=(id,)))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    actualUser = request.user
    listingData.watchlist.add(actualUser)
    return HttpResponseRedirect(reverse("listing", args=(id,)))

def watchlist(request):
    actualUser = request.user
    listings = actualUser.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings":listings
    })

def newComment(request, id):
    author = request.user
    listing = Listing.objects.get(pk=id)
    message = request.POST["newComment"]
    
    nComment = Comment(
        author = author,
        listing = listing,
        message = message
    )

    nComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id,)))


def displayCategory(request):
    if request.method == "POST":
        categories = Category.objects.all()
        categoryFiltered = Category.objects.get( categoryName = request.POST["category"])
        categoryListing = Listing.objects.filter( category = categoryFiltered, isActive = True)
        return render(request, "auctions/index.html", {
            "listings": categoryListing,
            "categories": categories
        })

def createListing(request):
    if request.method == "GET":
        categories = Category.objects.all()
        return render(request, "auctions/createlisting.html", {
            "categories": categories
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["image-url"]
        price = request.POST["price"]
        category = Category.objects.get(categoryName = request.POST["category"])

        actualUser = request.user

        bid = Bid(bid=float(price), user=actualUser)
        bid.save()

        newListing = Listing(
            title = title,
            description = description,
            image_url = imageurl,
            price = bid,
            owner = actualUser,
            category = category
        )

        newListing.save()

        return HttpResponseRedirect(reverse(index))

def newBid(request, id):
    actualUser = request.user
    nBid = float(request.POST["newBid"])
    listingData = Listing.objects.get(pk=id)
    userIsInWatch = request.user in listingData.watchlist.all()
    comments = Comment.objects.filter(listing=listingData)
    if nBid > listingData.price.bid:
        updatedBid = Bid(user=actualUser, bid=nBid)
        updatedBid.save()
        listingData.price = updatedBid
        listingData.winner = request.user.username
        listingData.save()
        return render(request, "auctions/listing.html", {
        "listing":listingData,
        "userIsInWatch":userIsInWatch,
        "comments":comments,
        "message":"Your bid was successfully added",
        "successBid":True
    })
    else:
        return render(request, "auctions/listing.html", {
        "listing":listingData,
        "userIsInWatch":userIsInWatch,
        "comments":comments,
        "message":"Your bid needs to be higher than the actual bid",
        "successBid":False
    })

    


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
