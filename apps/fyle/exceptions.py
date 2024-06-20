import logging
import traceback
from functools import wraps

from fyle.platform.exceptions import NoPrivilegeError, RetryException, InvalidTokenError as FyleInvalidTokenError
from rest_framework.response import Response
from rest_framework.views import status

from sage_desktop_sdk.exceptions.hh2_exceptions import WrongParamsError
from sage_desktop_api.exceptions import BulkError
from apps.workspaces.models import FyleCredential, Sage300Credential, Workspace, ExportSetting, AdvancedSetting

from apps.accounting_exports.models import AccountingExport


logger = logging.getLogger(__name__)
logger.level = logging.INFO


def handle_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FyleCredential.DoesNotExist:
            logger.info('Fyle credentials not found %s', args[0])  # args[1] is workspace_id
            args[1].detail = {'message': 'Fyle credentials do not exist in workspace'}
            args[1].status = 'FAILED'
            args[1].save()

        except NoPrivilegeError:
            logger.info('Invalid Fyle Credentials / Admin is disabled')
            args[1].detail = {'message': 'Invalid Fyle Credentials / Admin is disabled'}
            args[1].status = 'FAILED'
            args[1].save()

        except RetryException:
            logger.info('Fyle Retry Exception occured')
            args[1].detail = {'message': 'Fyle Retry Exception occured'}
            args[1].status = 'FATAL'
            args[1].save()

        except Exception:
            error = traceback.format_exc()
            args[1].detail = {'error': error}
            args[1].status = 'FATAL'
            args[1].save()
            logger.exception('Something unexpected happened workspace_id: %s %s', args[0], args[1].detail)

    return wrapper


def handle_view_exceptions():
    def decorator(func):
        def new_fn(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AccountingExport.DoesNotExist:
                return Response(data={'message': 'Expense group not found'}, status=status.HTTP_400_BAD_REQUEST)

            except FyleCredential.DoesNotExist:
                return Response(data={'message': 'Fyle credentials not found in workspace'}, status=status.HTTP_400_BAD_REQUEST)

            except FyleInvalidTokenError as exception:
                logger.info('Fyle token expired workspace_id - %s %s', kwargs['workspace_id'], {'error': exception.response})
                return Response(data={'message': 'Fyle token expired workspace_id'}, status=status.HTTP_400_BAD_REQUEST)

            except WrongParamsError as exception:
                logger.info('Sage token expired workspace_id - %s %s', kwargs['workspace_id'], {'error': exception.response})
                return Response(data={'message': 'Sage token expired workspace_id'}, status=status.HTTP_400_BAD_REQUEST)

            except NoPrivilegeError as exception:
                logger.info('Invalid Fyle Credentials / Admin is disabled  for workspace_id%s %s', kwargs['workspace_id'], {'error': exception.response})
                return Response(data={'message': 'Invalid Fyle Credentials / Admin is disabled'}, status=status.HTTP_400_BAD_REQUEST)

            except Workspace.DoesNotExist:
                return Response(data={'message': 'Workspace with this id does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            except AdvancedSetting.DoesNotExist:
                return Response(data={'message': 'Advanced Settings does not exist in workspace'}, status=status.HTTP_400_BAD_REQUEST)

            except ExportSetting.DoesNotExist:
                return Response({'message': 'Export Settings does not exist in workspace'}, status=status.HTTP_400_BAD_REQUEST)

            except Sage300Credential.DoesNotExist:
                logger.info('Sage credentials not found in workspace')
                return Response(data={'message': 'Sage credentials not found in workspace'}, status=status.HTTP_400_BAD_REQUEST)

            except BulkError as exception:
                logger.info('Bulk Error %s', exception.response)
                return Response(data={'message': 'Bulk Error'}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as exception:
                logger.exception(exception)
                return Response(data={'message': 'An unhandled error has occurred, please re-try later'}, status=status.HTTP_400_BAD_REQUEST)

        return new_fn

    return decorator
