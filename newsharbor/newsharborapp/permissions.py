from rest_framework import permissions

class IsEditorOrReadOnlyPermission(permissions.BasePermission):
    """
    Custom permission to only allow editors to edit or delete it.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.profile.is_editor
        else:
            return False

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.profile.is_editor
        else:
            return False

class EditorOnlyPermission(permissions.BasePermission):
    """
    Custom permission to grant access only to editors
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.profile.is_editor
        return False

    
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return request.user.profile.is_editor
        return False
    
class ArticleApiViewCustmoPermission(permissions.BasePermission):
    """
    Custom permission for specific view. Grants access to put method, only in case user sends arg "command"
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.profile.is_editor:
                return True
            else:
                command = request.data.get('command')
                if request.method == "PUT":
                    if command in ['like', 'dislike']:
                        return True
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user.profile.is_editor:
                return True
            else:
                command = request.data.get('command')
                if request.method == "PUT":
                    if command in ['like', 'dislike']:
                        return True
        return False
    
class CommentApiViewCustomPermission(permissions.BasePermission):
    """
    Custom permission for specific view. Grants access to put method, only in case user sends arg "command"
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            if request.user == obj.author:
                return True
            if request.user.profile.is_editor:
                return True
            else:
                command = request.data.get('command')
                if request.method == "PUT":
                    if command in ['like', 'dislike']:
                        return True
        return False
