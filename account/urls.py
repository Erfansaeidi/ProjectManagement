from django.urls import path

from .views import (
    HomeView,
    MyProfileDetailView,
    ProfilePictureDeleteView,
    ProfileUpdateView,
    SignUpView,
    UserProfileDetailView,
    WorkGroupAddMemberView,
    WorkGroupCreateView,
    WorkGroupDeleteView,
    WorkGroupDetailView,
    WorkGroupLeaveView,
    WorkGroupRemoveMemberView,
    WorkGroupTransferOwnershipView,
    WorkGroupUpdateView,
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', MyProfileDetailView.as_view(), name='my_profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/picture/delete/', ProfilePictureDeleteView.as_view(), name='profile_picture_delete'),
    path('profile/<int:user_id>/', UserProfileDetailView.as_view(), name='user_profile_detail'),
    path('group/', WorkGroupDetailView.as_view(), name='group_detail'),
    path('group/create/', WorkGroupCreateView.as_view(), name='group_create'),
    path('group/edit/', WorkGroupUpdateView.as_view(), name='group_edit'),
    path('group/delete/', WorkGroupDeleteView.as_view(), name='group_delete'),
    path('group/members/add/', WorkGroupAddMemberView.as_view(), name='group_add_member'),
    path('group/members/<int:user_id>/remove/', WorkGroupRemoveMemberView.as_view(), name='group_remove_member'),
    path('group/members/<int:user_id>/transfer/', WorkGroupTransferOwnershipView.as_view(), name='group_transfer_ownership'),
    path('group/leave/', WorkGroupLeaveView.as_view(), name='group_leave'),
]